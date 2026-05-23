import os, sys, json
import redis
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType
from pyspark.ml import PipelineModel

# ---------- Spark ----------
JAVA_HOME = os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-amd64")
os.environ["JAVA_HOME"] = JAVA_HOME
os.environ["PATH"] = JAVA_HOME + "/bin:" + os.environ.get("PATH", "")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

spark = SparkSession.builder \
    .appName("SpamStreamingSocket") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
    .config("spark.driver.extraJavaOptions",
            "--add-opens=java.base/java.lang=ALL-UNNAMED "
            "--add-opens=java.base/java.nio=ALL-UNNAMED "
            "--add-opens=java.base/java.util=ALL-UNNAMED "
            "-XX:+IgnoreUnrecognizedVMOptions") \
    .config("spark.executor.extraJavaOptions",
            "--add-opens=java.base/java.lang=ALL-UNNAMED "
            "--add-opens=java.base/java.nio=ALL-UNNAMED "
            "--add-opens=java.base/java.util=ALL-UNNAMED "
            "-XX:+IgnoreUnrecognizedVMOptions") \
    .getOrCreate()

# ---------- Модель ----------
print("Loading model...")
model = PipelineModel.load("models/spam_model_lr_ru")
print("Model loaded.")

# ---------- Redis ----------
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# ---------- TCP-сокет источник ----------
# Django будет отправлять JSON-строки на этот порт
SOCKET_HOST = "0.0.0.0"
SOCKET_PORT = 9999

print(f"Starting TCP stream on {SOCKET_HOST}:{SOCKET_PORT}...")
lines = spark.readStream \
    .format("socket") \
    .option("host", SOCKET_HOST) \
    .option("port", SOCKET_PORT) \
    .load()

# Схема JSON-сообщения
schema = StructType() \
    .add("task_id", StringType()) \
    .add("message", StringType()) \
    .add("hash", StringType())

# Парсим JSON из строки
parsed = lines.select(
    from_json(col("value"), schema).alias("data")
).select("data.*")

# Применяем модель
predictions = model.transform(parsed.withColumnRenamed("message", "email"))

# ---------- Запись результатов в Redis ----------
def write_to_redis(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    rows = batch_df.collect()
    for row in rows:
        task_id, msg_hash, prob = row.task_id, row.hash, float(row.probability[1])
        result = {'result': 'SPAM' if prob > 0.5 else 'NOT SPAM', 'probability': prob}
        redis_conn.setex(f"task:{task_id}:result", 3600, json.dumps(result))
        redis_conn.setex(f"task:{task_id}:status", 3600, "done")
        redis_conn.setex(f"spam_check:{msg_hash}", 86400, json.dumps(result))
    print(f"Batch {batch_id}: {len(rows)} messages")

# ---------- Запуск стриминга ----------
query = predictions.writeStream \
    .foreachBatch(write_to_redis) \
    .trigger(processingTime="100 milliseconds") \
    .outputMode("append") \
    .start()

print("Spark Streaming worker started, listening on socket 9999...")
query.awaitTermination()
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.types import StructType, StructField, StringType
import os
import sys
JAVA_HOME_PATH = "/usr/lib/jvm/java-17-openjdk-amd64"

# Установка критических переменных окружения
os.environ["JAVA_HOME"] = JAVA_HOME_PATH
os.environ["PATH"] = f"{JAVA_HOME_PATH}/bin:{os.environ['PATH']}"
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

spark = SparkSession.builder \
        .appName("SpamFilter") \
        .config("spark.driver.memory", "1g") \
        .config("spark.executor.memory", "1g") \
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
loaded_model = PipelineModel.load("../models/spam_model_lr")

test_emails = [
    "Congratulations! You won $1,000,000 lottery! Click here to claim",
    "Meeting reminder: Tomorrow at 10 AM in conference room",
    "Hi John, don't forget to submit your report by Friday",
    "Free viagra!!! Limited offer just for you",
    "Project status update and next steps"
]
schema = StructType([
    StructField("email", StringType(), True)
])
test_df = spark.createDataFrame([(email,) for email in test_emails], schema)
result = loaded_model.transform(test_df)
print("\nРезультаты классификации:")
print(result.select("email", "prediction").show(truncate=False))
spark.stop()
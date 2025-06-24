import os
import sys
import subprocess
from pyspark.sql import SparkSession

# 1. Настройка путей и окружения
# --------------------------------------------------
# Установите реальный путь к Java 17 (найдите с помощью: update-alternatives --list java)
JAVA_HOME_PATH = "/usr/lib/jvm/java-17-openjdk-amd64"

# Установка критических переменных окружения
os.environ["JAVA_HOME"] = JAVA_HOME_PATH
os.environ["PATH"] = f"{JAVA_HOME_PATH}/bin:{os.environ['PATH']}"
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# 2. Проверка окружения
# --------------------------------------------------
print("="*50)
print("Environment Diagnostics")
print("="*50)

# Проверка Java
try:
    java_version = subprocess.check_output(
        ["java", "-version"],
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    print(f"✓ Java version:\n{java_version}")
except Exception as e:
    print(f"✗ Java check failed: {e}")
    sys.exit(1)

# Проверка Python
print(f"✓ Python executable: {sys.executable}")
print(f"✓ Python version: {sys.version}")

# 3. Инициализация Spark с расширенной конфигурацией
# --------------------------------------------------
print("\n" + "="*50)
print("Initializing Spark Session")
print("="*50)

try:
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
    
    # 4. Проверка работоспособности Spark
    print(f"✓ Spark version: {spark.version}")
    sc = spark.sparkContext
    print(f"✓ Java version in Spark: {sc._jvm.java.lang.System.getProperty('java.version')}")
    
    # Тестовая операция
    data = [("Test", 1), ("Spark", 2)]
    df = spark.createDataFrame(data, ["Word", "Count"])
    print("✓ Simple DataFrame test:")
    print(df.show())
    
    print("\n✅ Spark initialized successfully!")

except Exception as e:
    print(f"\n❌ Spark initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Основная логика приложения
# --------------------------------------------------
try:
    print("\n" + "="*50)
    print("Running Spam Filter")
    print("="*50)
    
    # Здесь ваш код для работы с моделью
    # Например:
    # model = PipelineModel.load("path/to/model")
    # results = model.transform(your_data)
    # results.show()
    
    print("✅ Spam filter operations completed!")

except Exception as e:
    print(f"\n❌ Error in main application: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Всегда останавливаем Spark
    spark.stop()
    print("\n🛑 Spark session stopped")
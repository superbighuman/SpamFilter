from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
def menu(request:HttpRequest):
    return render(request,"menu.html")
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
import json
from django_redis import get_redis_connection
import time
import hashlib
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response
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
model = PipelineModel.load("models/spam_model_lr") #SpamFilter/Filter/views.py
def menu(request:HttpRequest):
    return render(request,"menu.html")
@swagger_auto_schema(
    method='post',
    operation_description="Определение спама на основе текста сообщения",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['message'],
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING, description='Текст сообщения'),
        },
    ),
    responses={
        200: openapi.Response(
            description="Результат предсказания",
            examples={
                "application/json": {
                    "status": "success",
                    "result": "SPAM",
                    "probability": 0.9432
                }
            }
        ),
        400: "Bad request"
    }
)
@csrf_exempt
@api_view(['POST'])
def predict(request):
    if request.method == 'POST':
        redis_conn = get_redis_connection("default")
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()

            if not message:
                return JsonResponse({'status': 'error', 'error': 'Empty message'})

            # Хешируем сообщение для использования как ключ Redis (безопаснее, короче)
            key = f"spam_check:{hashlib.sha256(message.encode()).hexdigest()}"

            # Попытка получить результат из Redis
            cached = redis_conn.get(key)
            if cached:
                result_data = json.loads(cached)
                return JsonResponse({'status': 'success', **result_data})

            # Если в Redis ничего не найдено — вызываем модель
            df = spark.createDataFrame([(message,)], ["email"])
            prediction = model.transform(df)

            result = prediction.select("prediction").collect()[0][0]
            probability = prediction.select("probability").collect()[0][0][1]

            result_data = {
                'result': 'SPAM' if result == 1 else 'NOT SPAM',
                'probability': probability
            }

            # Сохраняем результат в Redis (например, на 1 день — 86400 секунд)
            redis_conn.setex(key, 86400, json.dumps(result_data))

            return JsonResponse({'status': 'success', **result_data})

        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})

    return JsonResponse({'status': 'error', 'error': 'Invalid request method'})


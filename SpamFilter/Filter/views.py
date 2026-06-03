import json
import hashlib
import sys
import os

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from django_redis import get_redis_connection

from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view


os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

spark = SparkSession.builder \
    .appName("SpamFilter") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
    .config("spark.ui.showConsoleProgress", "false") \
    .getOrCreate()


model = PipelineModel.load("models/spam_model_lr_ru")

_ = spark.createDataFrame([("warmup",)], ["email"])
_ = model.transform(_).collect()


def menu(request: HttpRequest):
    return render(request, "menu.html")


@swagger_auto_schema(
    method='post',
    operation_description="Spam detection",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['message'],
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING)
        },
    ),
    responses={200: "OK"}
)
@csrf_exempt
@api_view(['POST'])
def predict(request):

    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()

        if not message:
            return JsonResponse({
                "status": "error",
                "error": "Empty message"
            })

        key = "spam:" + hashlib.sha256(message.encode()).hexdigest()

        redis_conn = None

        # Попытка подключения к Redis
        try:
            redis_conn = get_redis_connection("default")

            cached = redis_conn.get(key)

            if cached:
                return JsonResponse(json.loads(cached))

        except Exception as redis_error:
            print(f"Redis unavailable: {redis_error}")

        # Обработка моделью
        df = spark.createDataFrame([(message,)], ["email"])

        result_df = model.transform(df)

        row = result_df.select(
            "prediction",
            "probability"
        ).collect()[0]

        prediction = float(row["prediction"])
        probability = float(row["probability"][1])

        response = {
            "status": "success",
            "result": "SPAM" if probability > 0.5 else "NOT SPAM",
            "probability": probability
        }


        if redis_conn:
            try:
                redis_conn.setex(
                    key,
                    86400,
                    json.dumps(response)
                )
            except Exception as redis_error:
                print(f"Redis save error: {redis_error}")

        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e)
        })
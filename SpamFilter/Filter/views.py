import os, json, hashlib, uuid, socket
from django.shortcuts import render
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_redis import get_redis_connection

# Адрес Spark-воркера (имя контейнера в docker-compose)
SPARK_HOST = os.environ.get("SPARK_STREAMING_HOST", "spark-streaming")
SPARK_PORT = 9999

def menu(request: HttpRequest):
    return render(request, "menu.html")

@swagger_auto_schema(
    method='post',
    operation_description="Определение спама (асинхронный режим через сокет)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['message'],
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING, description='Текст сообщения'),
        },
    ),
    responses={
        202: openapi.Response(description="Задача принята в обработку"),
        200: openapi.Response(description="Результат из кеша"),
        400: "Bad request"
    }
)
@csrf_exempt
@api_view(['POST'])
def predict(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        if not message:
            return JsonResponse({'status': 'error', 'error': 'Empty message'}, status=400)

        redis_conn = get_redis_connection("default")
        msg_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()
        cache_key = f"spam_check:{msg_hash}"

        # Кеш
        cached = redis_conn.get(cache_key)
        if cached:
            result_data = json.loads(cached)
            return JsonResponse({'status': 'success', **result_data})

        # Новая задача
        task_id = uuid.uuid4().hex
        task_data = {
            'task_id': task_id,
            'message': message,
            'hash': msg_hash
        }
        redis_conn.setex(f"task:{task_id}:status", 300, "processing")

        # Отправка в сокет Spark-воркера
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((SPARK_HOST, SPARK_PORT))
            sock.sendall((json.dumps(task_data) + '\n').encode('utf-8'))
            sock.close()
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': f'Spark unavailable: {e}'}, status=500)

        return JsonResponse({'status': 'accepted', 'task_id': task_id}, status=202)

    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@swagger_auto_schema(
    method='get',
    operation_description="Получить результат по task_id",
    manual_parameters=[...],  # оставьте как есть
    responses={...}
)
@api_view(['GET'])
def get_result(request, task_id):
    redis_conn = get_redis_connection("default")
    status = redis_conn.get(f"task:{task_id}:status")
    if status is None:
        return JsonResponse({'status': 'error', 'error': 'Unknown task_id'}, status=404)
    status = status.decode()
    if status == "processing":
        return JsonResponse({'status': 'processing'})
    result_json = redis_conn.get(f"task:{task_id}:result")
    if result_json:
        result = json.loads(result_json)
        return JsonResponse({'status': 'success', **result})
    return JsonResponse({'status': 'error', 'error': 'Result missing'}, status=500)
# База: Python 3.12 на Debian (стабильный вариант)
FROM python:3.12-bookworm

# Чтобы apt не задавал вопросы
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка Java 17 (легкая версия)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk

# Рабочая директория
WORKDIR /app

# Сначала зависимости (чтобы кеш работал правильно)
COPY req_docker.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r req_docker.txt

# Копируем проект
COPY . .

# Порт Django
EXPOSE 8000

# Запуск Django
CMD ["python", "SpamFilter/manage.py", "runserver", "0.0.0.0:8000"]
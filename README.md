# Сервис для обнаружения спама в сообщениях

## Возможности
1. Классификация вредоносных сообщений на русском и английском языках с помощью методов машинного обучения
2. Интеграция в стороннее приложение с помощью API

## Зависимости
1. для сборки контейнера необходимо иметь docker и docker compose, поднять проект можно с помощью
```bash
  docker compose up --build -d 
  ```
2. Для запуска обучения моделей на другом наборе данных сначала необходимо создать виртуальное окружение
   
```basg
  python3 -m venv venv 
  ```
затем активировать виртуальное окружение
```bash
  source venv/bin/activate
  ```
и скачать зависимости через pip
```bash
pip3 install -r requirements.txt
```
3. Для разворачивания проекта без контейнера необходимо установить java-17
   ```bash
   apt-get update && \
    apt-get install -y openjdk-17-jdk
   ```
4. Для работы Jupyter достаточно прописать
   ```bash
   jupyter notebook
   ```
5. Для запуска веб-сервиса нужно будет запустить django
   ```bash
   python3 SpamFilter/manage.py runserver
   ```
## Результаты обучения моделей 
<img width="1142" height="576" alt="image" src="https://github.com/user-attachments/assets/d43c9c31-2e9c-4883-9b21-9fd53b47d544" />
<img width="854" height="636" alt="image" src="https://github.com/user-attachments/assets/8d86e625-0964-4e98-aa76-20f9dff6c8a7" />


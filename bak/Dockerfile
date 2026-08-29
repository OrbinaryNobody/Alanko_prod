FROM python:3.11-slim

WORKDIR /app

# копируем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# копируем весь проект
COPY ./app /app

# запускаем сервер
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
FROM python:3.11-slim

WORKDIR /app

# Сначала копируем только requirements — ускоряет сборку
COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Потом копируем весь проект
COPY . .

CMD ["python", "main.py"]


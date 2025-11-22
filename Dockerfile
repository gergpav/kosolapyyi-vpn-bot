FROM python:3.11-slim

WORKDIR /app

# Установка sqlite3
RUN apt update && apt install -y sqlite3 && apt clean

COPY . .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

CMD ["python", "main.py"]



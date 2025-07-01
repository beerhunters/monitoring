FROM python:3.11-slim

# Установка системных зависимостей для psycopg
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --timeout 100 -i https://mirrors.aliyun.com/pypi/simple/
COPY . .

CMD ["python", "-m", "bot.bot"]
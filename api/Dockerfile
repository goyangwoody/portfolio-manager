FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 (예: MySQL client)
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /app

CMD ["gunicorn", "main_new:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "--timeout", "120"]

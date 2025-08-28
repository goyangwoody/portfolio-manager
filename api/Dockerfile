FROM python:3.11-slim
WORKDIR /app

# 루트 기준의 경로 사용
COPY api/requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev curl && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir -r requirements.txt

COPY api/ .        
COPY src/ /app/src/

# src를 찾을 수 있도록 파이썬 경로 추가
ENV PYTHONPATH=/app

# API 디렉토리에서 실행되게(정적 파일 경로 등 고려)
WORKDIR /app/api

# gunicorn 실행 (파일명/앱명 맞는지 확인: main_new:app)
CMD ["gunicorn","main_new:app","-k","uvicorn.workers.UvicornWorker","-w","2","-b","0.0.0.0:8000","--timeout","120"]
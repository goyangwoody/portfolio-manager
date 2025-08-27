FROM python:3.11-slim

WORKDIR /app
# (선택) 빌드에 필요한 OS 패키지
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev curl && rm -rf /var/lib/apt/lists/*

# 루트의 requirements.txt를 먼저 복사/설치
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드와 공유모듈 복사
COPY api/ /app/api/
COPY src/ /app/src/

# src를 찾을 수 있도록 파이썬 경로 추가
ENV PYTHONPATH=/app

# API 디렉토리에서 실행되게(정적 파일 경로 등 고려)
WORKDIR /app/api

# gunicorn 실행 (파일명/앱명 맞는지 확인: main_new:app)
CMD ["gunicorn","main_new:app","-k","uvicorn.workers.UvicornWorker","-w","2","-b","0.0.0.0:8000","--timeout","120"]
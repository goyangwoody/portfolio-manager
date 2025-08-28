FROM python:3.11-slim

# 성능/로그
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 코드 기준 디렉터리 = /app  (← 중요)
WORKDIR /app

# 루트 컨텍스트 기준 경로로 requirements 설치
COPY api/requirements.txt ./requirements.txt
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev curl \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir "uvicorn[standard]" gunicorn

# 코드 복사: /app 에 main_new.py, /app/src/* 들어오게
COPY api/ .
COPY src/ /app/src/

# /app/src 임포트 위해 PYTHONPATH=/app  (← 이미 잘 되어있음)
ENV PYTHONPATH=/app

# 포트 노출
EXPOSE 8000

# ★ 핵심: /app을 작업 디렉터리로 유지, 모듈 경로는 main_new:app
# (main_new.py가 /app에 존재하는 것이 확인됨)
CMD ["gunicorn","main_new:app","-k","uvicorn.workers.UvicornWorker","-w","2","-b","0.0.0.0:8000","--timeout","120"]

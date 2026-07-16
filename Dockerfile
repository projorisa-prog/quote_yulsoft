FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. requirements.txt 안의 git+https:// 링크 처리를 위해 런타임에 git 설치 추가
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    fonts-noto-cjk \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. 의존성 파일 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. 소스 코드 복사
COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
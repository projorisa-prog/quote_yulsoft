# 1. 컴파일 부담이 없는 가벼운 Python 기본 이미지 사용
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 2. 필수 시스템 의존성 최소화 설치 (오버헤드 방지)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 3. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 복사 (구조에 맞게 매칭)
# 만약 main.py가 app/ 폴더 안에 있다면 아래 구조를 유지합니다.
COPY ./app ./app

EXPOSE 8000

# 5. 메모리를 적게 먹도록 워커 수를 1개로 제한하여 기본 uvicorn 구동
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
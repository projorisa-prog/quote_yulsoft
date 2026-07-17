# Use python:3.11-slim-bookworm (debian base, avoids Docker Hub rate limits)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies: libpq-dev (postgres), fonts-noto-cjk (WeasyPrint Korean PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from pyproject.toml (NOT requirements.txt)
COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install .

# Copy application code
COPY ./app ./app

EXPOSE 8000

# Production: gunicorn with single worker (memory efficient for free tier)
# 호스트는 반드시 0.0.0.0으로 열어야 외부(Render)와 통신이 가능합니다.
# 포트는 Render가 주입해 주는 $PORT 환경 변수를 우선 따르도록 하고, 없을 경우 10000(또는 8000)을 기본값으로 씁니다.
CMD ["sh", "-c", "gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-10000} --timeout 120"]
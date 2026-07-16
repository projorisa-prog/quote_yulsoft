The user wants me to apply the suggested edit to the original code. The suggested edit is a complete rewrite of the Dockerfile, not just a patch. I need to output the complete modified file based on the suggested edit.

Looking at the suggested edit, it's a complete Dockerfile that replaces the original. I should output the suggested edit as the complete modified file.

Wait, the instruction says "Apply the SUGGESTED EDIT to the ORIGINAL CODE. Output the complete modified file." and "Leave existing comments in place unless changes require modifying them."

The suggested edit has different comments and structure. It seems like the suggested edit is the new version to use. I should output the suggested edit as the complete file.

Let me check the suggested edit carefully - it's a complete Dockerfile with different stages and commands. I'll output it as-is since that's what "apply the suggested edit" means in this context.# Build Stage
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 시스템 의존성 (WeasyPrint용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY pyproject.toml .
RUN pip install --prefix=/install .


# Runtime Stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

# 런타임 의존성만 설치 (크기 최소화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/*
# 비루트 유저 생성
RUN useradd --create-home --shell /bin/bash appuser
# 빌드된 패키지 복사
COPY --from=builder /install /usr/local

# 애플리케이션 코드 복사
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .

USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=3).raise_for_status()"

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--graceful-timeout", "30"]

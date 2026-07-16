from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from app.core.config import settings
from app.db.session import engine
from app.db.init_db import init_db
from app.api.v1 import quotes, auth, users, templates
from app.core.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    print("🚀 Starting Yulsoft Quote System...")
    # 개발 편의를 위해 테이블 자동 생성 (프로덕션은 Alembic 사용)
    if settings.APP_ENV == "development":
        await init_db()
    yield
    # 종료 시
    print("🛑 Shutting down...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="율소프트 청소 견적 프로그램 API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# 예외 핸들러 설정
setup_exception_handlers(app)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (CSS, JS, 폰트 등)
app.mount(
    "/static",
    StaticFiles(directory=settings.STATIC_DIR),
    name="static",
)

# API 라우터 등록
app.include_router(quotes.router, prefix=f"{settings.API_V1_PREFIX}/quotes", tags=["Quotes"])
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(templates.router, prefix=f"{settings.API_V1_PREFIX}/templates", tags=["Templates"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "yulsoft-quote"}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "율소프트 견적 프로그램 API",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1,
    )
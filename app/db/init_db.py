import asyncio
from sqlalchemy import text
from app.db.session import engine, Base
from app.models import quote, user  # noqa: F401 (모델 임포트 필수 - 테이블 생성 위해)


async def init_db() -> None:
    """데이터베이스 테이블 생성 (개발/테스트용)
    프로덕션에서는 Alembic 마이그레이션 사용 권장"""
    async with engine.begin() as conn:
        # PostgreSQL 확장 기능 활성화 (UUID 생성 등)
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        # 테이블 생성
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully.")


async def drop_db() -> None:
    """테이블 전체 삭제 (테스트용)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("🗑️ Database tables dropped.")


if __name__ == "__main__":
    asyncio.run(init_db())
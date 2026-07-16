import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserPlan(str, PyEnum):
    FREE = "FREE"           # 무료 체험 (워터마크 있음)
    PRO = "PRO"             # 월 구독 (워터마크 제거, 템플릿 저장)
    ENTERPRISE = "ENTERPRISE" # ERP 연동, 전용 지원


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_biz_reg_no", "biz_reg_no", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True
    )

    # 인증
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # 플랜
    plan: Mapped[UserPlan] = mapped_column(
        Enum(UserPlan, native_enum=False),
        default=UserPlan.FREE,
        nullable=False,
    )

    # 회사 정보 (공급자 정보로 자동 채워짐)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ceo_name: Mapped[str] = mapped_column(String(100), nullable=False)
    biz_reg_no: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)  # 하이픈 없는 10자리
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 업태
    business_item: Mapped[str] = mapped_column(String(200), nullable=False)  # 종목
    company_address: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {postal, address, detail}
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # 견적번호 시퀀스 (회원별 독립)
    quote_seq: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 관계
    quotes: Mapped[List["Quote"]] = relationship(back_populates="user", lazy="dynamic")
    templates: Mapped[List["Template"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class CompanyInfo(Base):
    """공급자 정보 별도 관리 (회사 이력 관리용)"""
    __tablename__ = "company_infos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    biz_reg_no: Mapped[str] = mapped_column(String(10), nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ceo_name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)
    business_item: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    is_default: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship()


class Template(Base):
    """자주 쓰는 견적 항목 템플릿 (유료 기능)"""
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 예: "표준 주 2회 오피스 청소"
    items: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)  # QuoteItem 스키마 리스트
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)  # 공유 템플릿 여부

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="templates")
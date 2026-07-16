The user wants me to apply the suggested edit to the original code. The suggested edit is a complete rewrite of the file with additional models (User, QuoteTemplate) and changes to existing models (Quote, QuoteItem). I need to output the complete modified file based on the suggested edit.

Let me analyze the suggested edit and apply it properly. The suggested edit includes:
1. New imports (enum, timedelta, Decimal, DeclarativeBase, expression, JSONB)
2. New Base class using DeclarativeBase
3. Updated QuoteStatus and DesignTemplate enums
4. New User model
5. Updated Quote model with changes (user_id type changed to UUID, JSONB columns, relationship changes, new indexes)
6. Updated QuoteItem model with JSONB for days column
6. New QuoteTemplate model

I should output the complete file as per the suggested edit, since it's a comprehensive rewrite```python
import enum
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String, Integer, Text, DateTime, Enum, ForeignKey, Index, func, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.sql import expression


class Base(DeclarativeBase):
    pass
class QuoteStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # 작성 중 (비회원 임시 저장 등)
    COMPLETED = "COMPLETED"   # 완성됨 (PDF 생성 완료, 공유 가능)
    CONVERTED = "CONVERTED"   # 계약서로 전환됨 (유료 회원)
    EXPIRED = "EXPIRED"       # 유효기간 만료


class DesignTemplate(str, enum.Enum):
    CLASSIC = "classic"   # 클래식/관공서용
    MODERN = "modern"     # 모던/애플 스타일 (기본)
    COLOR = "color"       # 컬러 포인트/젊은 감각


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ceo_name: Mapped[str] = mapped_column(String(100), nullable=False)
    biz_reg_no: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)  # 하이픈 제외 10자리

    # 주소 분리 저장 (검색/필터용)
    address_postal: Mapped[str] = mapped_column(String(10), nullable=True)
    address_main: Mapped[str] = mapped_column(Text, nullable=True)
    address_detail: Mapped[str] = mapped_column(Text, nullable=True)

    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    plan: Mapped[str] = mapped_column(String(20), default="FREE", nullable=False)  # FREE, PRO, ENTERPRISE
    quote_seq: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 견적번호 자동증가용

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    quotes: Mapped[List["Quote"]] = relationship(back_populates="owner", lazy="dynamic")
    templates: Mapped[List["QuoteTemplate"]] = relationship(back_populates="owner", lazy="dynamic")


class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4
    )
    quote_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    status: Mapped[QuoteStatus] = mapped_column(
        Enum(QuoteStatus, native_enum=False), default=QuoteStatus.DRAFT, nullable=False, index=True
    )
    design_key: Mapped[DesignTemplate] = mapped_column(
        Enum(DesignTemplate, native_enum=False), default=DesignTemplate.MODERN, nullable=False
    )

    # JSONB로 유연하게 저장 (스냅샷)
    customer_info: Mapped[dict] = mapped_column(JSONB, nullable=False)
    supplier_info: Mapped[dict] = mapped_column(JSONB, nullable=False)
    calculation_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)  # 재계산/수정용 원본 입력값

    # 계산 결과 캐시 (빠른 조회용)
    totals: Mapped[dict] = mapped_column(JSONB, nullable=False)

    watermark_text: Mapped[str] = mapped_column(Text, default="Powered by 율소프트", nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner: Mapped[Optional["User"]] = relationship(back_populates="quotes")
    items: Mapped[List["QuoteItem"]] = relationship(back_populates="quote", cascade="all, delete-orphan", order_by="QuoteItem.sort_order")

    __table_args__ = (
        Index("ix_quotes_user_created", "user_id", "created_at"),
        Index("ix_quotes_status_expires", "status", "expires_at"),
    )


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    area: Mapped[str] = mapped_column(String(100), nullable=False)
    task: Mapped[str] = mapped_column(String(200), nullable=False)
    days: Mapped[List[str]] = mapped_column(JSONB, nullable=False)  # ["MON", "WED"]
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exclude_area: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    memo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    quote: Mapped["Quote"] = relationship(back_populates="items")


class QuoteTemplate(Base):
    """자주 쓰는 항목 템플릿 (유료 기능)"""
    __tablename__ = "quote_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    items: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)  # QuoteItemInput 리스트
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="templates")

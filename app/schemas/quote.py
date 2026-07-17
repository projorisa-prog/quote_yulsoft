import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.db.session import Base


class QuoteStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CONVERTED = "CONVERTED"
    EXPIRED = "EXPIRED"


class ServiceType(str, enum.Enum):
    REGULAR = "REGULAR"
    ONE_TIME = "ONE_TIME"
    MOVE_IN = "MOVE_IN"
    OFFICE = "OFFICE"
    POST_CONSTRUCTION = "POST_CONSTRUCTION"
    CUSTOM = "CUSTOM"


class Frequency(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    ONCE = "ONCE"


class DayOfWeek(str, enum.Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    quotes: Mapped[List["Quote"]] = relationship("Quote", back_populates="owner", lazy="selectin")
    templates: Mapped[List["QuoteTemplate"]] = relationship("QuoteTemplate", back_populates="owner", lazy="selectin")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4)
    quote_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)

    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[QuoteStatus] = mapped_column(SQLEnum(QuoteStatus), default=QuoteStatus.DRAFT, nullable=False, index=True)
    design_type: Mapped[str] = mapped_column(String(20), default="modern", nullable=False)

    # Customer Info (JSONB snapshot)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_info: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Supplier Info (JSONB snapshot)
    supplier_name: Mapped[str] = mapped_column(String(255), default="율소프트", nullable=False)
    supplier_ceo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supplier_biz_num: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_fax: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    supplier_bank: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supplier_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supplier_holder: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supplier_info: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Service Details
    service_type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType), default=ServiceType.REGULAR, nullable=False)
    service_area_pyung: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    staff_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    frequency: Mapped[Optional[Frequency]] = mapped_column(SQLEnum(Frequency), nullable=True)
    days_of_week: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    service_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    work_hours: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Pricing (원 단위 정수)
    unit_price: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(default=Decimal("0.10"), nullable=False)
    discount_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    supply_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    vat_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Calculation snapshot (JSONB)
    calculation_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    totals: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Validity & Conversion
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    converted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    contract_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    owner: Mapped[Optional["User"]] = relationship("User", back_populates="quotes", lazy="selectin")
    items: Mapped[List["QuoteItem"]] = relationship("QuoteItem", back_populates="quote", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_quotes_owner_status", "owner_id", "status"),
        Index("ix_quotes_public_id", "public_id"),
    )


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), default="식", nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_price: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_taxable: Mapped[bool] = mapped_column(default=True, nullable=False)

    # For recurring services
    frequency: Mapped[Optional[Frequency]] = mapped_column(SQLEnum(Frequency), nullable=True)
    days_of_week: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="items", lazy="selectin")


class QuoteTemplate(Base):
    __tablename__ = "quote_templates"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    design_type: Mapped[str] = mapped_column(String(20), default="modern", nullable=False)
    template_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner: Mapped["User"] = relationship("User", back_populates="templates", lazy="selectin")

    __table_args__ = (
        Index("ix_templates_owner_default", "owner_id", "is_default"),
    )
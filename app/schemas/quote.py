"from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator


class DayOfWeek(str, Enum):
    MON = \"MON\"
    TUE = \"TUE\"
    WED = \"WED\"
    THU = \"THU\"
    FRI = \"FRI\"
    SAT = \"SAT\"
    SUN = \"SUN\"


class PresetFrequency(str, Enum):
    WEEKLY_1 = \"WEEKLY_1\"   # 주 1회
    WEEKLY_2 = \"WEEKLY_2\"   # 주 2회
    WEEKLY_3 = \"WEEKLY_3\"   # 주 3회
    WEEKLY_5 = \"WEEKLY_5\"   # 주 5회 (월~금)
    DAILY = \"DAILY\"         # 매일


PRESET_DAYS_MAP = {
    PresetFrequency.WEEKLY_1: [DayOfWeek.MON],
    PresetFrequency.WEEKLY_2: [DayOfWeek.MON, DayOfWeek.THU],
    PresetFrequency.WEEKLY_3: [DayOfWeek.MON, DayOfWeek.WED, DayOfWeek.FRI],
    PresetFrequency.WEEKLY_5: [DayOfWeek.MON, DayOfWeek.TUE, DayOfWeek.WED, DayOfWeek.THU, DayOfWeek.FRI],
    PresetFrequency.DAILY: list(DayOfWeek),
}


class CustomerInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description=\"고객명\")
    phone: str = Field(..., pattern=r\"^01[0-9]-?\\d{4}-?\\d{4}$\", description=\"연락처\")
    email: Optional[EmailStr] = Field(None, description=\"이메일\")
    address: str = Field(..., min_length=5, max_length=200, description=\"주소\")
    detail_address: Optional[str] = Field(None, max_length=100, description=\"상세주소\")
    building_type: Literal[\"APT\", \"OFFICETEL\", \"OFFICE\", \"STORE\", \"FACTORY\", \"ETC\"] = Field(..., description=\"건물 유형\")
    area_pyeong: Optional[float] = Field(None, ge=0, description=\"평수 (면적 단가 계산용)\")


class SupplierInfo(BaseModel):
    biz_reg_no: str = Field(..., pattern=r\"^\\d{10}$\", description=\"사업자등록번호 (하이픈 제외 10자리)\")
    company_name: str = Field(..., min_length=1, max_length=200, description=\"상호\")
    ceo_name: str = Field(..., min_length=1, max_length=100, description=\"대표자 성명\")
    address: str = Field(..., min_length=5, max_length=500, description=\"소재지\")
    business_type: str = Field(..., min_length=1, max_length=100, description=\"업태\")
    business_item: str = Field(..., min_length=1, max_length=200, description=\"종목\")
    phone: str = Field(..., pattern=r\"^0[0-9]{1,2}-?\\d{3,4}-?\\d{4}$\", description=\"전화번호\")
    email: EmailStr = Field(..., description=\"이메일\")


class QuoteItemInput(BaseModel):
    area: str = Field(..., min_length=1, max_length=100, description=\"청소구역\")
    task: str = Field(..., min_length=1, max_length=200, description=\"청소내용\")
    days: List[DayOfWeek] = Field(..., min_items=1, description=\"요일 리스트\")
    qty: int = Field(1, ge=1, le=100, description=\"수량/횟수\")
    unit_price: int = Field(0, ge=0, le=100_000_000, description=\"단가 (원)\")
    exclude_area: Optional[str] = Field(None, max_length=200, description=\"제외구역\")
    memo: Optional[str] = Field(None, max_length=500, description=\"비고\")

    @property
    def total_price(self) -> int:
        return self.qty * self.unit_price


class CalculationInput(BaseModel):
    items: List[QuoteItemInput] = Field(..., min_items=1, description=\"견적 항목 리스트\")
    discount_type: Literal[\"NONE\", \"PERCENT\", \"AMOUNT\"] = Field(\"NONE\", description=\"할인 유형\")
    discount_value: int = Field(0, ge=0, description=\"할인 값 (퍼센트 또는 금액)\")
    vat_included: bool = Field(False, description=\"단가 VAT 포함 여부\")
    vat_rate: Decimal = Field(Decimal(\"0.1\"), description=\"부가세율\")


class Totals(BaseModel):
    subtotal: int = Field(..., description=\"공급가액 합계\")
    discount_amount: int = Field(..., description=\"할인 금액\")
    taxable_amount: int = Field(..., description=\"과세표준 (공급가액 - 할인)\")
    vat_amount: int = Field(..., description=\"부가세액\")
    grand_total: int = Field(..., description=\"총 견적 금액 (과세표준 + 부가세)\")


class QuoteCreateRequest(BaseModel):
    customer: CustomerInfo
    supplier: Optional[SupplierInfo] = None  # 비회원은 필수, 회원은 선택 (DB에서 조회)
    calculation: CalculationInput
    design_key: Literal[\"classic\", \"modern\", \"color\"] = Field(\"modern\", description=\"디자인 템플릿\")
    expires_days: int = Field(30, ge=1, le=365, description=\"유효기간 (일)\")
    preset_frequency: Optional[PresetFrequency] = Field(None, description=\"UI 프리셋 버튼용 (서버에서 days로 변환)\")

    @model_validator(mode='after')
    def apply_preset(self) -> 'QuoteCreateRequest':
        if self.preset_frequency and self.calculation.items:
            preset_days = PRESET_DAYS_MAP[self.preset_frequency]
            for item in self.calculation.items:
                # 프리셋이 선택되면 요일 강제 덮어쓰기
                item.days = preset_days
        return self


class QuotePreviewResponse(BaseModel):
    \"\"\"미리보기용 (DB 저장 안 함)\"\"\"
    items: List[QuoteItemInput]
    totals: Totals
    design_key: str
    expires_at: datetime


class QuoteItemResponse(QuoteItemInput):
    id: int
    sort_order: int
    total_price: int

    class Config:
        from_attributes = True


class QuoteResponse(BaseModel):
    \"\"\"견적서 조회 응답 (웹 뷰/PDF 생성용)\"\"\"
    public_id: UUID
    quote_number: str
    status: str
    design_key: str
    watermark_text: str
    customer_info: CustomerInfo
    supplier_info: SupplierInfo
    items: List[QuoteItemResponse]
    totals: Totals
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteListResponse(BaseModel):
    public_id: UUID
    quote_number: str
    status: str
    customer_name: str
    grand_total: int
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True"

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple
from app.schemas.quote import CalculationInput, QuoteItemInput, Totals


VAT_RATE = Decimal("0.1")


def calculate_totals(data: CalculationInput) -> Tuple[List[QuoteItemInput], Totals]:
    """
    견적서 금액 계산 엔진 (결정론적, 정수 연산 기반)
    
    Args:
        data: 계산 입력값 (항목 리스트, 할인, 부가세 설정)
    
    Returns:
        Tuple[items_with_total, totals]
        - items_with_total: total_price가 계산된 항목 리스트
        - totals: 소계, 할인, 과세표준, 부가세, 총계
    """
    items = data.items
    subtotal = 0
    
    # 1. 품목별 금액 계산 (정수 연산)
    for item in items:
        item.total_price = item.qty * item.unit_price
        subtotal += item.total_price
    
    # 2. 할인 계산
    discount_amount = 0
    if data.discount_type == "PERCENT" and data.discount_value > 0:
        # 퍼센트 할인: 소계 * 퍼센트 / 100 (원단위 반올림)
        discount_amount = int((Decimal(str(subtotal)) * Decimal(str(data.discount_value)) / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    elif data.discount_type == "AMOUNT" and data.discount_value > 0:
        # 금액 할인: 소계를 초과하지 않도록 제한
        discount_amount = min(data.discount_value, subtotal)
    
    taxable_amount = subtotal - discount_amount
    
    # 3. 부가세 계산 (국세청 기준: 공급가액 * 0.1, 원단위 반올림)
    vat_amount = int((Decimal(str(taxable_amount)) * VAT_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    
    grand_total = taxable_amount + vat_amount
    
    totals = Totals(
        subtotal=subtotal,
        discount_amount=discount_amount,
        taxable_amount=taxable_amount,
        vat_amount=vat_amount,
        grand_total=grand_total
    )
    
    return items, totals


def generate_quote_number(user_seq: int, year_month: str = None) -> str:
    """견적번호 생성: YYMM-SEQ (예: 2407-0001)"""
    from datetime import datetime
    if year_month is None:
        year_month = datetime.now().strftime("%y%m")
    return f"{year_month}-{user_seq:04d}"


def calculate_expires_at(days: int = 30) -> datetime:
    """유효기간 계산 (기본 30일)"""
    from datetime import datetime, timedelta
    return datetime.now() + timedelta(days=days)
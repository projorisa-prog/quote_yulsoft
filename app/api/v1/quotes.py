from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.session import get_db
from app.services.calculation import calculate_totals
from app.models.quote import Quote, QuoteItem, QuoteStatus, DesignTemplate, User
from app.schemas.quote import (
    QuoteCreateRequest,
    QuotePreviewResponse,
    QuoteResponse,
    QuoteListResponse,
    Totals,
)
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()


# ====================================================================
# Helper Functions
# ====================================================================

def generate_quote_number(user: User) -> str:
    """견적번호 생성: YYMM-SEQ (예: 2412-0001)"""
    user.quote_seq += 1
    yymm = datetime.now().strftime("%y%m")
    return f"{yymm}-{user.quote_seq:04d}"


def get_watermark_text(user: Optional[User]) -> str:
    """워터마크 텍스트 결정"""
    if not user or user.plan == "FREE":
        return "Powered by 율소프트 | www.yulsoft.kr"
    return ""


def calculate_expires_at(days: int) -> datetime:
    return datetime.utcnow() + timedelta(days=days)


async def build_quote_response(quote: Quote) -> QuoteResponse:
    """Quote ORM -> Response Schema 변환"""
    items = [
        {
            **item.__dict__,
            "days": item.days,
        }
        for item in quote.items
    ]
    
    return QuoteResponse(
        public_id=quote.public_id,
        quote_number=quote.quote_number,
        status=quote.status.value,
        design_key=quote.design_key.value,
        watermark_text=quote.watermark_text,
        customer_info=quote.customer_info,
        supplier_info=quote.supplier_info,
        items=items,
        totals=quote.totals,
        expires_at=quote.expires_at,
        created_at=quote.created_at,
    )


# ====================================================================
# API Endpoints
# ====================================================================

@router.post(
    "/preview",
    response_model=QuotePreviewResponse,
    summary="견적 미리보기 (저장 안 함)",
    description="DB 저장 없이 계산 로직만 실행하여 미리보기용 데이터 반환",
)
async def preview_quote(request: QuoteCreateRequest):
    """비회원/회원 모두 사용 가능. DB 저장 없음."""
    items, totals = calculate_totals(request.calculation)
    
    # 공급자 정보: 요청에 있으면 사용, 없으면 기본값
    supplier_info = request.supplier.dict() if request.supplier else {
        "company_name": "율소프트",
        "ceo_name": "대표자",
        "biz_reg_no": "0000000000",
        "address": "서울시",
        "business_type": "서비스",
        "business_item": "청소업",
        "phone": "02-0000-0000",
        "email": "info@yulsoft.kr",
    }
    
    expires_at = calculate_expires_at(request.expires_days)
    
    return QuotePreviewResponse(
        items=items,
        totals=totals,
        design_key=request.design_key,
        expires_at=expires_at,
    )


@router.post(
    "",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="견적서 생성 및 저장",
)
async def create_quote(
    request: QuoteCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """견적서 생성 후 DB 저장. 비회원은 임시 저장, 회원은 정식 저장."""
    
    # 1. 계산 수행
    items, totals = calculate_totals(request.calculation)
    
    # 2. 공급자 정보 결정
    if current_user:
        # 회원: DB 정보 사용 (요청 무시)
        supplier_info = {
            "biz_reg_no": current_user.biz_reg_no,
            "company_name": current_user.company_name,
            "ceo_name": current_user.ceo_name,
            "address": f"{current_user.address_postal or ''} {current_user.address_main or ''} {current_user.address_detail or ''}".strip(),
            "business_type": "서비스",  # 추후 확장
            "business_item": "청소업",
            "phone": current_user.phone or "",
            "email": current_user.email,
        }
        quote_number = generate_quote_number(current_user)
        watermark = get_watermark_text(current_user)
        user_id = current_user.id
    else:
        # 비회원: 요청 필수
        if not request.supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비회원은 공급자 정보(supplier)가 필수입니다."
            )
        supplier_info = request.supplier.dict()
        quote_number = f"TEMP-{uuid.uuid4().hex[:8].upper()}"
        watermark = get_watermark_text(None)
        user_id = None
    
    # 3. 견적서 객체 생성
    expires_at = calculate_expires_at(request.expires_days)
    
    quote = Quote(
        public_id=uuid.uuid4(),
        quote_number=quote_number,
        user_id=user_id,
        status=QuoteStatus.COMPLETED,
        design_key=DesignTemplate(request.design_key),
        customer_info=request.customer.dict(),
        supplier_info=supplier_info,
        calculation_snapshot=request.calculation.dict(),
        totals=totals.dict(),
        watermark_text=watermark,
        expires_at=expires_at,
    )
    
    # 4. 항목 추가
    for idx, item in enumerate(items):
        quote.items.append(QuoteItem(
            sort_order=idx,
            area=item.area,
            task=item.task,
            days=[d.value for d in item.days],
            qty=item.qty,
            unit_price=item.unit_price,
            total_price=item.total_price,
            exclude_area=item.exclude_area,
            memo=item.memo,
        ))
    
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    
    return await build_quote_response(quote)


@router.get(
    "/{public_id}",
    response_model=QuoteResponse,
    summary="견적서 조회 (공개용)",
    description="Public ID로 견적서 조회. 비회원 공유 링크용.",
)
async def get_quote(public_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Quote).options(selectinload(Quote.items)).where(Quote.public_id == public_id)
    result = await db.execute(stmt)
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="견적서를 찾을 수 없습니다.")
    
    if quote.status == QuoteStatus.EXPIRED or quote.expires_at < datetime.utcnow():
        quote.status = QuoteStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=410, detail="유효기간이 만료된 견적서입니다.")
    
    return await build_quote_response(quote)


@router.get(
    "/{public_id}/pdf",
    summary="PDF 다운로드",
    description="견적서 PDF 파일 생성 및 다운로드",
)
async def download_pdf(public_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """PDF 생성 엔드포인트 (WeasyPrint 사용)"""
    from app.services.pdf_generator import generate_pdf
    from fastapi.responses import StreamingResponse
    import io
    
    stmt = select(Quote).options(selectinload(Quote.items)).where(Quote.public_id == public_id)
    result = await db.execute(stmt)
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="견적서를 찾을 수 없습니다.")
    
    pdf_bytes = await generate_pdf(quote)
    
    filename = f"견적서_{quote.quote_number}_{quote.customer_info.get('name', '')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


# ====================================================================
# 회원 전용 API
# ====================================================================

@router.get(
    "",
    response_model=List[QuoteListResponse],
    summary="내 견적서 목록 조회",
)
async def list_my_quotes(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Quote).where(Quote.user_id == current_user.id)
    
    if status:
        stmt = stmt.where(Quote.status == QuoteStatus(status.upper()))
    
    stmt = stmt.order_by(desc(Quote.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    quotes = result.scalars().all()
    
    return [
        QuoteListResponse(
            public_id=q.public_id,
            quote_number=q.quote_number,
            status=q.status.value,
            customer_name=q.customer_info.get("name", ""),
            grand_total=q.totals.get("grand_total", 0),
            expires_at=q.expires_at,
            created_at=q.created_at,
        )
        for q in quotes
    ]


@router.patch(
    "/{quote_id}",
    response_model=QuoteResponse,
    summary="견적서 수정 (작성자만, DRAFT/COMPLETED 상태만)",
)
async def update_quote(
    quote_id: int,
    request: QuoteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Quote).options(selectinload(Quote.items)).where(Quote.id == quote_id, Quote.user_id == current_user.id)
    result = await db.execute(stmt)
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="견적서를 찾을 수 없습니다.")
    
    if quote.status not in [QuoteStatus.DRAFT, QuoteStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="수정할 수 없는 상태입니다.")
    
    # 재계산
    items, totals = calculate_totals(request.calculation)
    
    # 업데이트
    quote.customer_info = request.customer.dict()
    quote.calculation_snapshot = request.calculation.dict()
    quote.totals = totals.dict()
    quote.design_key = DesignTemplate(request.design_key)
    quote.expires_at = calculate_expires_at(request.expires_days)
    quote.updated_at = datetime.utcnow()
    
    # 기존 항목 삭제 후 새로 추가
    for item in quote.items:
        await db.delete(item)
    
    for idx, item in enumerate(items):
        quote.items.append(QuoteItem(
            sort_order=idx,
            area=item.area,
            task=item.task,
            days=[d.value for d in item.days],
            qty=item.qty,
            unit_price=item.unit_price,
            total_price=item.total_price,
            exclude_area=item.exclude_area,
            memo=item.memo,
        ))
    
    await db.commit()
    await db.refresh(quote)
    
    return await build_quote_response(quote)

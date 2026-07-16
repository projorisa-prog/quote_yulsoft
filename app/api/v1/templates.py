from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.models.quote import QuoteTemplate, User
from app.api.deps import get_current_user

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    items: List[dict]
    is_default: bool = False


class TemplateResponse(BaseModel):
    id: int
    name: str
    items: List[dict]
    is_default: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """내 템플릿 목록 조회"""
    stmt = select(QuoteTemplate).where(QuoteTemplate.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """템플릿 생성 (유료 기능)"""
    if current_user.plan == "FREE":
        raise HTTPException(status_code=403, detail="PRO 플랜 이상에서 이용 가능합니다.")
    
    template = QuoteTemplate(
        user_id=current_user.id,
        name=data.name,
        items=data.items,
        is_default=data.is_default,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """템플릿 삭제"""
    stmt = select(QuoteTemplate).where(QuoteTemplate.id == template_id, QuoteTemplate.user_id == current_user.id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")
    
    await db.delete(template)
    await db.commit()
    return {"message": "삭제되었습니다."}
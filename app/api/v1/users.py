from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db.session import get_db
from app.models.quote import User
from app.api.deps import get_current_user

router = APIRouter()


class CompanyInfoUpdate(BaseModel):
    company_name: Optional[str] = None
    ceo_name: Optional[str] = None
    biz_reg_no: Optional[str] = None
    address_postal: Optional[str] = None
    address_main: Optional[str] = None
    address_detail: Optional[str] = None
    phone: Optional[str] = None
    business_type: Optional[str] = None
    business_item: Optional[str] = None


@router.get("/me/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """내 프로필/회사 정보 조회"""
    return {
        "email": current_user.email,
        "company_name": current_user.company_name,
        "ceo_name": current_user.ceo_name,
        "biz_reg_no": current_user.biz_reg_no,
        "address_postal": current_user.address_postal,
        "address_main": current_user.address_main,
        "address_detail": current_user.address_detail,
        "phone": current_user.phone,
        "plan": current_user.plan,
        "quote_seq": current_user.quote_seq,
    }


@router.patch("/me/profile")
async def update_profile(
    data: CompanyInfoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """회사 정보 수정"""
    for field, value in data.dict(exclude_unset=True).items():
        if field == "biz_reg_no" and value:
            value = value.replace("-", "")
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    return {"message": "수정되었습니다."}
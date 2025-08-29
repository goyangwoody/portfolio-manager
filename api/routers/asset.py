from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services.asset import AssetService
from schemas.asset import AssetPriceHistoryResponse

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/{asset_id}/price-history", response_model=AssetPriceHistoryResponse)
async def get_asset_price_history(
    asset_id: int,
    start_date: Optional[date] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    days: int = Query(30, ge=1, le=365, description="조회할 일수 (기본 30일)"),
    db: Session = Depends(get_db)
):
    """
    자산의 가격 히스토리 조회
    
    - **asset_id**: 조회할 자산 ID
    - **start_date**: 시작 날짜 (선택사항)
    - **end_date**: 종료 날짜 (선택사항, 기본값: 오늘)
    - **days**: 조회할 일수 (start_date가 없을 때 사용)
    
    Returns:
        자산의 일별 가격 히스토리
    """
    try:
        asset_service = AssetService(db)
        result = asset_service.get_asset_price_history(
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date,
            days=days
        )
        
        if not result.prices:
            raise HTTPException(
                status_code=404,
                detail=f"Asset {asset_id}에 대한 가격 데이터를 찾을 수 없습니다."
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

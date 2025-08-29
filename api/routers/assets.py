"""
Asset-focused API endpoints with date-based queries and sorting
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from enum import Enum

from database import get_db
from schemas.assets import AssetInfo
from schemas.holdings import CurrentHolding, HoldingsResponse
from schemas.common import AssetFilter

router = APIRouter(prefix="/portfolios/{portfolio_id}/assets", tags=["assets"])

class SortField(str, Enum):
    """자산 정렬 기준"""
    NAME = "name"
    AVG_PRICE = "avgPrice"
    CURRENT_PRICE = "currentPrice"
    DAY_CHANGE = "dayChange"
    TOTAL_RETURN = "totalReturn"
    MARKET_VALUE = "marketValue"

class SortDirection(str, Enum):
    """정렬 방향"""
    ASC = "asc"
    DESC = "desc"

@router.get("", response_model=List[CurrentHolding])
async def get_portfolio_assets(
    portfolio_id: int,
    as_of_date: Optional[date] = Query(None, description="기준일 (기본값: 최신일)"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터"),
    sort_by: SortField = Query(SortField.NAME, description="정렬 기준"),
    sort_direction: SortDirection = Query(SortDirection.ASC, description="정렬 방향"),
    search: Optional[str] = Query(None, description="자산명/티커 검색"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 자산 목록 조회 (날짜별 + 정렬 + 검색)
    - as_of_date: 특정 날짜의 자산 현황 조회 (기본값: 최신일)
    - sort_by: 정렬 기준 선택
    - sort_direction: 오름차순/내림차순
    - search: 자산명이나 티커로 검색
    """
    try:
        from services.assets import get_portfolio_assets_service
        return await get_portfolio_assets_service(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            asset_filter=asset_filter,
            sort_by=sort_by,
            sort_direction=sort_direction,
            search=search,
            db=db
        )
    except Exception as e:
        print(f"Error in get_portfolio_assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{asset_id}", response_model=CurrentHolding)
async def get_asset_detail(
    portfolio_id: int,
    asset_id: int,
    as_of_date: Optional[date] = Query(None, description="기준일 (기본값: 최신일)"),
    db: Session = Depends(get_db)
):
    """개별 자산 상세 정보 조회"""
    try:
        from services.assets import get_asset_detail_service
        return await get_asset_detail_service(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            as_of_date=as_of_date,
            db=db
        )
    except Exception as e:
        print(f"Error in get_asset_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{asset_id}/price-history")
async def get_asset_price_history(
    portfolio_id: int,
    asset_id: int,
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"), 
    interval: str = Query("daily", description="간격 (daily/weekly/monthly)"),
    db: Session = Depends(get_db)
):
    """자산 가격 히스토리 조회 (차트용)"""
    try:
        from services.assets import get_asset_price_history_service
        return await get_asset_price_history_service(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            db=db
        )
    except Exception as e:
        print(f"Error in get_asset_price_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 전역 자산 검색 (포트폴리오 무관)
@router.get("/search", response_model=List[AssetInfo])
async def search_assets(
    q: str = Query(description="검색어 (자산명, 티커)"),
    limit: int = Query(20, le=100, description="결과 개수 제한"),
    db: Session = Depends(get_db)
):
    """전역 자산 검색"""
    try:
        from services.assets import search_assets_service
        return await search_assets_service(
            query=q,
            limit=limit,
            db=db
        )
    except Exception as e:
        print(f"Error in search_assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

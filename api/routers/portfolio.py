"""
Portfolio overview and holdings API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from database import get_db
from schemas import (
    PortfoliosResponse, PortfolioHoldingsResponse, AssetDetailResponse,
    TimePeriod
)
from services.portfolio import (
    get_portfolios_service, get_portfolio_holdings_service,
    get_asset_detail_service
)

router = APIRouter(tags=["portfolios"])

@router.get("/portfolios", response_model=PortfoliosResponse)
async def get_portfolios(
    include_kpi: bool = Query(True, description="KPI 데이터 포함 여부"),
    include_chart: bool = Query(False, description="차트 데이터 포함 여부 (Hero Cover 섹션용)"),
    portfolio_type: Optional[str] = Query(None, description="core 또는 usd_core"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 목록 조회 (Hero Cover 섹션용)
    - include_kpi=false: 기본 목록만 (포트폴리오 선택용)
    - include_kpi=true: KPI 포함된 요약 정보
    - include_chart=true: NAV 차트 데이터 포함 (Overview 페이지용)
    - portfolio_type: core(ID:1) / usd_core(ID:3) 필터링
    """
    try:
        return await get_portfolios_service(include_kpi, include_chart, portfolio_type, db)
    except Exception as e:
        print(f"Error in get_portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolios/{portfolio_id}/holdings", response_model=PortfolioHoldingsResponse)
async def get_portfolio_holdings(
    portfolio_id: int,
    as_of_date: Optional[date] = Query(None, description="기준일 (기본값: 최신일)"),
    db: Session = Depends(get_db)
):
    """포트폴리오 보유 자산 현황 조회 (Assets 페이지용)"""
    try:
        return await get_portfolio_holdings_service(portfolio_id, as_of_date, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_portfolio_holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolios/{portfolio_id}/assets/{asset_id}", response_model=AssetDetailResponse)
async def get_asset_detail(
    portfolio_id: int,
    asset_id: int,
    period: TimePeriod = Query(TimePeriod.INCEPTION, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """개별 자산 상세 정보 조회 (Assets 페이지 디테일 시트용)"""
    try:
        return await get_asset_detail_service(portfolio_id, asset_id, period, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_asset_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TODO: Risk & Allocation 엔드포인트 구현 필요
# @router.get("/portfolios/{portfolio_id}/risk-allocation", response_model=RiskAndAllocationResponse)
# async def get_risk_and_allocation(
#     portfolio_id: int,
#     period: TimePeriod = Query(TimePeriod.INCEPTION, description="분석 기간"),
#     db: Session = Depends(get_db)
# ):
#     """포트폴리오 리스크 및 배분 현황 조회 (Risk & Allocation 페이지용) - 현재 미구현"""
#     try:
#         return await get_risk_and_allocation_service(portfolio_id, period, db)
#     except Exception as e:
#         print(f"Error in get_risk_and_allocation: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

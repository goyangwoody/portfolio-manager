"""
Risk analysis endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date as Date, datetime
from typing import Optional

from database import get_db
from schemas.risk import (
    RiskAnalysisResponse,
    PortfolioRiskMetrics,
    AssetRiskContribution,
    CorrelationMatrix,
    StressTestResponse,
    AssetAllocationResponse,
    AssetClassAllocation,
    AssetClassDetailsResponse
)
from schemas.common import AssetFilter, TimePeriod
from services.risk import RiskService

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/allocation/{portfolio_id}", response_model=AssetAllocationResponse, summary="자산 배분 현황")
async def get_asset_allocation(
    portfolio_id: int,
    as_of_date: Optional[Date] = Query(None, description="기준일 (기본값: 최신일)"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오의 자산군별 배분 현황을 조회합니다.
    
    자산군(asset_class)별로 그룹화하여 다음 정보를 제공합니다:
    - 자산군별 배분 비중
    - 자산군별 구성 자산 목록
    - 시장가치 및 비중 정보
    """
    try:
        risk_service = RiskService(db)
        result = await risk_service.get_asset_allocation(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            asset_filter=asset_filter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자산 배분 조회 실패: {str(e)}")

@router.get("/allocation/{portfolio_id}/class/{asset_class}", response_model=AssetClassDetailsResponse, summary="자산군별 상세 정보")
async def get_asset_class_details(
    portfolio_id: int,
    asset_class: str,
    as_of_date: Optional[Date] = Query(None, description="기준일 (기본값: 최신일)"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터"),
    db: Session = Depends(get_db)
):
    """
    특정 자산군의 상세 정보를 조회합니다.
    
    선택된 자산군에 속한 모든 자산의 상세 정보를 제공합니다:
    - 개별 자산 포지션 정보 (수량, 평균 매입가, 현재가)
    - 수익률 정보 (일간 변동, 총 수익률, 미실현 손익)
    - 자산군 통계 정보
    """
    try:
        risk_service = RiskService(db)
        result = await risk_service.get_asset_class_details_new(
            portfolio_id=portfolio_id,
            asset_class=asset_class,
            as_of_date=as_of_date,
            asset_filter=asset_filter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자산군 상세 정보 조회 실패: {str(e)}")

@router.get("/analysis/{portfolio_id}", response_model=RiskAnalysisResponse, summary="리스크 분석")
async def get_risk_analysis(
    portfolio_id: int,
    period: TimePeriod = Query(TimePeriod.ALL, description="분석 기간"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터"),
    confidence_level: float = Query(0.95, description="신뢰수준", ge=0.01, le=0.99),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 리스크 분석을 수행합니다.
    
    다음 지표들을 계산합니다:
    - 포트폴리오 변동성, 샤프비율, 최대낙폭
    - VaR (Value at Risk)
    - 자산별 리스크 기여도
    """
    try:
        risk_service = RiskService(db)
        result = await risk_service.analyze_portfolio_risk(
            portfolio_id=portfolio_id,
            period=period,
            asset_filter=asset_filter,
            confidence_level=confidence_level
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리스크 분석 실패: {str(e)}")

@router.get("/correlation/{portfolio_id}", response_model=CorrelationMatrix, summary="상관관계 분석")
async def get_correlation_analysis(
    portfolio_id: int,
    period: TimePeriod = Query(TimePeriod.ONE_YEAR, description="분석 기간"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 내 자산간 상관관계를 분석합니다.
    
    자산간 수익률 상관계수를 계산하여 분산투자 효과를 분석합니다.
    """
    try:
        risk_service = RiskService(db)
        result = await risk_service.analyze_asset_correlation(
            portfolio_id=portfolio_id,
            period=period,
            asset_filter=asset_filter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상관관계 분석 실패: {str(e)}")

@router.get("/stress-test/{portfolio_id}", response_model=StressTestResponse, summary="스트레스 테스트")
async def run_stress_test(
    portfolio_id: int,
    scenario: str = Query("market_crash", description="시나리오 유형"),
    as_of_date: Optional[Date] = Query(None, description="기준일"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 스트레스 테스트를 수행합니다.
    
    다양한 시장 시나리오 하에서 포트폴리오의 손실 가능성을 분석합니다.
    """
    try:
        risk_service = RiskService(db)
        result = await risk_service.run_stress_test(
            portfolio_id=portfolio_id,
            scenario=scenario,
            as_of_date=as_of_date,
            asset_filter=asset_filter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트레스 테스트 실패: {str(e)}")

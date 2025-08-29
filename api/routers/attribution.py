"""
Attribution analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from database import get_db
from schemas import (
    AttributionAllTimeResponse, AttributionSpecificPeriodResponse, 
    AttributionCustomPeriodResponse, AssetDetailResponse, AssetFilter, TimePeriod
)
from services.attribution import (
    calculate_detailed_twr_attribution, calculate_asset_detail
)
from src.pm.db.models import Portfolio, PortfolioPositionDaily

router = APIRouter(prefix="/portfolios/{portfolio_id}/attribution", tags=["attribution"])

@router.get("/all-time", response_model=AttributionAllTimeResponse)
async def get_portfolio_attribution_all_time(
    portfolio_id: int,
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터 (all/domestic/foreign)"),
    db: Session = Depends(get_db)
):
    """포트폴리오 All Time 기여도 분석 (TWR 기반)"""
    try:
        # 포트폴리오 존재 여부 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # 전체 기간 설정 (첫 포지션부터 최신일까지)
        from sqlalchemy import desc
        first_position = db.query(PortfolioPositionDaily).filter(
            PortfolioPositionDaily.portfolio_id == portfolio_id
        ).order_by(PortfolioPositionDaily.as_of_date).first()
        
        latest_position = db.query(PortfolioPositionDaily).filter(
            PortfolioPositionDaily.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioPositionDaily.as_of_date)).first()
        
        if not first_position or not latest_position:
            raise HTTPException(status_code=404, detail="No position data found")
        
        start_date = first_position.as_of_date
        end_date = latest_position.as_of_date
        
        # TWR 기반 기여도 계산 (필터 적용)
        attribution_result = calculate_detailed_twr_attribution(
            db, portfolio_id, start_date, end_date, asset_filter
        )
        
        return AttributionAllTimeResponse(
            total_twr=attribution_result["total_twr"],
            daily_returns=attribution_result["daily_returns"],
            asset_class_contributions=attribution_result["asset_class_contributions"],
            top_contributors=attribution_result["top_contributors"],
            top_detractors=attribution_result["top_detractors"],
            asset_filter=asset_filter,
            period=TimePeriod.ALL,
            start_date=start_date,
            end_date=end_date,
            total_contribution_check=attribution_result.get("total_contribution_check")
        )
        
    except Exception as e:
        print(f"Error in get_portfolio_attribution_all_time: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/specific-period", response_model=AttributionSpecificPeriodResponse)
async def get_portfolio_attribution_specific_period(
    portfolio_id: int,
    start_date: date = Query(description="분석 시작일"),
    end_date: date = Query(description="분석 종료일"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터 (all/domestic/foreign)"),
    period_type: str = Query("custom", description="기간 타입 (week/month/custom)"),
    db: Session = Depends(get_db)
):
    """포트폴리오 Specific Period 기여도 분석 (TWR 기반)"""
    try:
        # 포트폴리오 존재 여부 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # 날짜 유효성 검사
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        # 해당 기간에 데이터가 있는지 확인
        from sqlalchemy import and_
        position_count = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.as_of_date >= start_date,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).count()
        
        if position_count == 0:
            raise HTTPException(status_code=404, detail="No position data found for the specified period")
        
        # TWR 기반 기여도 계산 (필터 적용)
        attribution_result = calculate_detailed_twr_attribution(
            db, portfolio_id, start_date, end_date, asset_filter
        )
        
        return AttributionSpecificPeriodResponse(
            period_twr=attribution_result["total_twr"],
            daily_returns=attribution_result["daily_returns"],
            asset_class_contributions=attribution_result["asset_class_contributions"],
            top_contributors=attribution_result["top_contributors"],
            top_detractors=attribution_result["top_detractors"],
            asset_filter=asset_filter,
            start_date=start_date,
            end_date=end_date,
            period_type=period_type,
            total_contribution_check=attribution_result.get("total_contribution_check")
        )
        
    except Exception as e:
        print(f"Error in get_portfolio_attribution_specific_period: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/asset-detail/{asset_id}", response_model=AssetDetailResponse)
async def get_attribution_asset_detail(
    portfolio_id: int,
    asset_id: int,
    start_date: Optional[date] = Query(None, description="분석 시작일 (기본값: All Time)"),
    end_date: Optional[date] = Query(None, description="분석 종료일 (기본값: 최신일)"),
    db: Session = Depends(get_db)
):
    """개별 자산 상세 정보 조회 (드릴다운용)"""
    try:
        # 포트폴리오와 자산 존재 여부 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        from src.pm.db.models import Asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # 기간 설정
        if not start_date or not end_date:
            from sqlalchemy import and_, desc
            first_position = db.query(PortfolioPositionDaily).filter(
                and_(
                    PortfolioPositionDaily.portfolio_id == portfolio_id,
                    PortfolioPositionDaily.asset_id == asset_id
                )
            ).order_by(PortfolioPositionDaily.as_of_date).first()
            
            latest_position = db.query(PortfolioPositionDaily).filter(
                and_(
                    PortfolioPositionDaily.portfolio_id == portfolio_id,
                    PortfolioPositionDaily.asset_id == asset_id
                )
            ).order_by(desc(PortfolioPositionDaily.as_of_date)).first()
            
            if not first_position or not latest_position:
                raise HTTPException(status_code=404, detail="No position data found for this asset")
            
            start_date = start_date or first_position.as_of_date
            end_date = end_date or latest_position.as_of_date
        
        # 자산 상세 정보 계산
        asset_detail = calculate_asset_detail(
            db, portfolio_id, asset_id, start_date, end_date
        )
        
        return asset_detail
        
    except Exception as e:
        print(f"Error in get_attribution_asset_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

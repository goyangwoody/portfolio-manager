"""
Portfolio performance API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas import PerformanceAllTimeResponse, PerformanceCustomPeriodResponse
from services.performance import get_performance_all_time, get_performance_custom_period

router = APIRouter(prefix="/portfolios/{portfolio_id}/performance", tags=["performance"])

@router.get("")
async def get_portfolio_performance(
    portfolio_id: int,
    period: str = Query("all", description="분석 기간"),
    custom_week: Optional[str] = Query(None, description="커스텀 주차 (YYYY-WNN 형식)"),
    custom_month: Optional[str] = Query(None, description="커스텀 월 (YYYY-MM 형식)"),
    chart_period: Optional[str] = Query("all", description="차트 기간 (all/1m/1w) - All Time에서만 사용"),
    db: Session = Depends(get_db)
):
    """포트폴리오 성과 데이터 조회 (Performance 페이지용)"""
    try:
        # All time 기간에 대한 특별 처리
        if period == "all":
            return await get_performance_all_time(portfolio_id, chart_period, db)
        
        # Custom 기간에 대한 처리
        elif period == "custom":
            return await get_performance_custom_period(portfolio_id, custom_week, custom_month, db)
        
        # 다른 기간들은 향후 구현
        else:
            return {"message": f"Period '{period}' not yet implemented"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_portfolio_performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

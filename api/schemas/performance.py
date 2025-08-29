"""
Performance analysis schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from .common import TimePeriod

# ================================
# PERFORMANCE SCHEMAS
# ================================

class RecentReturnData(BaseModel):
    """최근 수익률 데이터 (All Time용)"""
    daily_return: Optional[float] = Field(None, description="1일 수익률 (%)")
    weekly_return: Optional[float] = Field(None, description="1주 수익률 (%)")
    monthly_return: Optional[float] = Field(None, description="1개월 수익률 (%)")
    
    # 추가 기간 수익률
    day_1: Optional[float] = Field(None, description="1일 수익률 (%) - Backend")
    week_1: Optional[float] = Field(None, description="1주 수익률 (%) - Backend")
    month_1: Optional[float] = Field(None, description="1개월 수익률 (%) - Backend")
    month_3: Optional[float] = Field(None, description="3개월 수익률 (%)")
    month_6: Optional[float] = Field(None, description="6개월 수익률 (%)")
    year_1: Optional[float] = Field(None, description="1년 수익률 (%)")
    daily_returns: Optional[List["DailyReturnPoint"]] = Field(None, description="최근 일별 수익률")

class DailyReturnPoint(BaseModel):
    """일별 수익률 차트 포인트"""
    date: date
    daily_return: float = Field(description="일별 수익률 (%)")
    
    # Backend compatibility
    return_pct: Optional[float] = Field(None, description="일별 수익률 (%) - Backend")

class BenchmarkReturn(BaseModel):
    """벤치마크 수익률 데이터"""
    name: str = Field(description="벤치마크 이름")
    symbol: str = Field(description="벤치마크 심볼")
    return_pct: float = Field(description="벤치마크 수익률 (%)")
    excess_return: float = Field(description="포트폴리오 대비 초과수익률 (%)")
    
    # Frontend compatibility
    outperformance: Optional[float] = Field(None, description="아웃퍼포먼스 (%) - Frontend")
    difference: Optional[float] = Field(None, description="차이 (%) - Backend")

class PerformanceAllTimeResponse(BaseModel):
    """All Time 성과 데이터 응답"""
    recent_returns: RecentReturnData = Field(description="최근 1일/1주/1개월 수익률")
    recent_week_daily_returns: List[DailyReturnPoint] = Field(description="최근 주간 일별 수익률")
    daily_returns: List[DailyReturnPoint] = Field(description="차트 기간에 따른 일별 수익률")
    benchmark_returns: List[BenchmarkReturn] = Field(description="벤치마크 대비 수익률")
    start_date: Optional[date] = Field(None, description="분석 시작일")
    end_date: Optional[date] = Field(None, description="분석 종료일")

class PerformanceCustomPeriodResponse(BaseModel):
    """Custom Period 성과 데이터 응답"""
    cumulative_return: float = Field(description="기간 누적 수익률 (%)")
    daily_returns: List[DailyReturnPoint] = Field(description="기간 중 일별 수익률")
    benchmark_returns: List[BenchmarkReturn] = Field(description="기간 중 벤치마크 대비 수익률")
    start_date: date = Field(description="분석 시작일")
    end_date: date = Field(description="분석 종료일")
    period_type: str = Field(description="기간 타입 (week/month)")

class PerformanceDataPoint(BaseModel):
    """성과 차트용 개별 데이터 포인트 (다른 기간용)"""
    date: date
    portfolio_value: float = Field(description="포트폴리오 가치")
    benchmark_value: Optional[float] = Field(None, description="벤치마크 가치")
    daily_return: Optional[float] = Field(None, description="일일 수익률 (%)")
    
    class Config:
        from_attributes = True

class PerformanceResponse(BaseModel):
    """성과 데이터 응답 (일반 기간용)"""
    data: List[PerformanceDataPoint]
    period: TimePeriod
    start_date: date
    end_date: date
    
    # 요약 통계
    total_return: Optional[float] = Field(None, description="기간 총 수익률 (%)")
    annualized_return: Optional[float] = Field(None, description="연환산 수익률 (%)")
    volatility: Optional[float] = Field(None, description="변동성 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="샤프 비율")

# Legacy compatibility
PerformanceData = PerformanceDataPoint

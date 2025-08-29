"""
Portfolio overview and listing schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import date

from .common import TimePeriod

# ================================
# PORTFOLIO SCHEMAS
# ================================

class PortfolioListResponse(BaseModel):
    """기본 포트폴리오 목록 응답 (포트폴리오 선택용)"""
    id: int
    name: str
    currency: str
    
    class Config:
        from_attributes = True

class PortfolioSummaryResponse(PortfolioListResponse):
    """KPI 지표가 포함된 포트폴리오 응답 (Overview 페이지용)"""
    # 핵심 KPI
    total_return: Optional[float] = Field(None, description="총 수익률 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="샤프 비율")
    nav: Optional[float] = Field(None, description="순자산가치")
    cash_ratio: Optional[float] = Field(None, description="현금 비중 (%)")

class NavChartDataPoint(BaseModel):
    """NAV 차트용 데이터 포인트"""
    date: date
    nav: float = Field(description="순자산가치")
    benchmark: Optional[float] = Field(None, description="벤치마크 값 (기준값 100)")
    
    class Config:
        from_attributes = True

class PortfolioWithChartResponse(PortfolioSummaryResponse):
    """차트 데이터가 포함된 포트폴리오 응답 (Overview 페이지용)"""
    chart_data: List[NavChartDataPoint] = Field(description="NAV 차트 데이터")

class PortfoliosResponse(BaseModel):
    """포트폴리오 목록 응답 래퍼"""
    portfolios: List[Union[PortfolioListResponse, PortfolioSummaryResponse, PortfolioWithChartResponse]]
    total_count: Optional[int] = Field(None, description="총 포트폴리오 수")

# Legacy compatibility
PortfolioResponse = PortfolioSummaryResponse

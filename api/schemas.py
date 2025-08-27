"""
Pydantic schemas for API responses
Based on frontend requirements and SQLAlchemy models
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

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
    total_return: Optional[float] = None    # 총 수익률 (%)
    sharpe_ratio: Optional[float] = None    # 샤프 비율
    nav: Optional[float] = None             # 순자산가치
    aum: Optional[float] = None             # 총 자산 관리 규모


# ================================
# PERFORMANCE SCHEMAS
# ================================

class PerformanceDataResponse(BaseModel):
    """성과 차트용 데이터"""
    date: date
    portfolio_value: float
    benchmark_value: float
    daily_return: Optional[float] = None
    
    class Config:
        from_attributes = True


# ================================
# ASSET & HOLDINGS SCHEMAS  
# ================================

class AssetResponse(BaseModel):
    """기본 자산 정보"""
    id: int
    ticker: str
    name: Optional[str] = None
    currency: str
    asset_class: Optional[str] = None
    
    class Config:
        from_attributes = True


class AssetHoldingResponse(BaseModel):
    """포트폴리오 보유 자산 (계산된 값 포함)"""
    id: int
    name: str
    ticker: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    day_change: float           # 일일 변동률 (%)
    weight: float              # 포트폴리오 내 비중 (%)


# ================================
# ATTRIBUTION SCHEMAS
# ================================

class AssetClassAttributionResponse(BaseModel):
    """자산군별 기여도 분석"""
    id: str                    # unique identifier
    asset_class: str           # 자산군명
    allocation: float          # 비중 (%)
    contribution: float        # 기여도 (%)


class TopContributorResponse(BaseModel):
    """상위 기여자/하락자"""
    id: str
    name: str
    contribution: float        # 기여도 (%)
    weight: float             # 비중 (%)
    return_rate: float        # 수익률 (%)
    type: str                 # "contributor" | "detractor"


# ================================
# API WRAPPER SCHEMAS
# ================================

class PortfolioHoldingsResponse(BaseModel):
    """포트폴리오 보유 자산 전체 응답"""
    holdings: List[AssetHoldingResponse]
    total_market_value: float
    cash_balance: float
    total_value: float


class AttributionAnalysisResponse(BaseModel):
    """기여도 분석 전체 응답"""
    asset_class_attribution: List[AssetClassAttributionResponse]
    top_contributors: List[TopContributorResponse]
    top_detractors: List[TopContributorResponse]

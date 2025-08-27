from pydantic import BaseModel
from typing import List, Optional

# ================================
# 포트폴리오 메인 API
# ================================

class PortfolioSummary(BaseModel):
    """Overview 페이지에서 필요한 모든 포트폴리오 데이터"""
    id: int
    name: str
    currency: str
    
    # KPI 카드 데이터
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None  
    nav: Optional[float] = None
    cash_ratio: Optional[float] = None    # 현금 비중 (%) - AUM 대신 추가
    
    # 추가 지표 (필요시 사용)
    volatility: Optional[float] = None
    max_drawdown: Optional[float] = None
    beta: Optional[float] = None

    class Config:
        from_attributes = True

class PortfoliosResponse(BaseModel):
    """포트폴리오 목록 응답"""
    portfolios: List[PortfolioSummary]

# ================================
# 포트폴리오 타입별 필터링 지원
# ================================

class PortfolioListItem(BaseModel):
    """포트폴리오 선택용 간단한 정보"""
    id: int
    name: str
    currency: str
    portfolio_type: Optional[str] = None  # "domestic" | "foreign"

    class Config:
        from_attributes = True

# ================================  
# 성능 차트 API
# ================================

class PerformancePoint(BaseModel):
    """차트용 성능 데이터 포인트"""
    date: str  # YYYY-MM-DD 형식
    portfolioValue: float
    benchmarkValue: float

    class Config:
        from_attributes = True

class PerformanceResponse(BaseModel):
    """성능 차트 데이터 응답"""
    data: List[PerformancePoint]

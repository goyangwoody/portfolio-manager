"""
PortfolioPulse API v3.0 Schemas
Mobile-first portfolio management API for external reporting
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from datetime import date
from enum import Enum

# ================================
# COMMON ENUMS & TYPES
# ================================

class TimePeriod(str, Enum):
    """분석 기간 옵션"""
    INCEPTION = "inception"      # 투자 시작부터
    YTD = "ytd"                 # 연초부터
    ONE_MONTH = "1m"            # 1개월
    THREE_MONTHS = "3m"         # 3개월
    SIX_MONTHS = "6m"           # 6개월
    ONE_YEAR = "1y"             # 1년

class PortfolioType(str, Enum):
    """포트폴리오 타입"""
    CORE = "core"           # Core 포트폴리오 (ID: 1)
    USD_CORE = "usd_core"   # USD Core 포트폴리오 (ID: 3)

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

# ================================
# PERFORMANCE SCHEMAS
# ================================

class PerformanceDataPoint(BaseModel):
    """성과 차트용 개별 데이터 포인트"""
    date: date
    portfolio_value: float = Field(description="포트폴리오 가치")
    benchmark_value: Optional[float] = Field(None, description="벤치마크 가치")
    daily_return: Optional[float] = Field(None, description="일일 수익률 (%)")
    
    class Config:
        from_attributes = True

class PerformanceResponse(BaseModel):
    """성과 데이터 응답"""
    data: List[PerformanceDataPoint]
    period: TimePeriod
    start_date: date
    end_date: date
    
    # 요약 통계
    total_return: Optional[float] = Field(None, description="기간 총 수익률 (%)")
    annualized_return: Optional[float] = Field(None, description="연환산 수익률 (%)")
    volatility: Optional[float] = Field(None, description="변동성 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="샤프 비율")

# ================================
# ATTRIBUTION SCHEMAS
# ================================

class AssetClassAttributionResponse(BaseModel):
    """자산 클래스별 기여도 분석"""
    asset_class: str = Field(description="자산 클래스명")
    weight: Optional[float] = Field(None, description="비중 (%)")
    return_contribution: Optional[float] = Field(None, description="수익 기여도 (%)")
    total_contribution: Optional[float] = Field(None, description="총 기여도 (%)")

class AssetAttributionResponse(BaseModel):
    """개별 자산 기여도 분석"""
    asset_id: int
    ticker: str
    name: str
    weight: Optional[float] = Field(None, description="비중 (%)")
    return_contribution: Optional[float] = Field(None, description="수익 기여도 (%)")
    total_contribution: Optional[float] = Field(None, description="총 기여도 (%)")

class AttributionResponse(BaseModel):
    """기여도 분석 응답"""
    asset_class_attributions: List[AssetClassAttributionResponse]
    top_contributors: List[AssetAttributionResponse] = Field(description="상위 기여 자산")
    period: TimePeriod
    start_date: date
    end_date: date

# ================================
# HOLDINGS & ASSETS SCHEMAS
# ================================

class AssetHoldingResponse(BaseModel):
    """포트폴리오 보유 자산 정보"""
    id: int
    name: str
    ticker: str
    quantity: float = Field(description="보유 수량")
    avg_price: float = Field(description="평균 취득가")
    current_price: float = Field(description="현재가")
    market_value: float = Field(description="시장가치")
    unrealized_pnl: float = Field(description="미실현 손익")
    day_change: float = Field(description="일일 변동률 (%)")
    weight: float = Field(description="포트폴리오 내 비중 (%)")

class PortfolioHoldingsResponse(BaseModel):
    """포트폴리오 보유 현황 응답"""
    holdings: List[AssetHoldingResponse]
    total_market_value: float = Field(description="총 시장가치")
    cash_balance: float = Field(description="현금 잔고")
    total_value: float = Field(description="총 가치 (시장가치 + 현금)")
    as_of_date: date = Field(description="기준일")

class PriceHistoryPoint(BaseModel):
    """가격 히스토리 포인트"""
    date: date
    price: float

class AssetDetailResponse(BaseModel):
    """개별 자산 상세 정보 (Assets 페이지 디테일 시트용)"""
    id: int
    name: str
    ticker: str
    currency: str
    asset_class: Optional[str] = None
    
    # 포지션 정보
    quantity: float = Field(description="보유 수량")
    avg_cost: float = Field(description="평균 취득가")
    current_price: float = Field(description="현재가")
    unrealized_pnl: float = Field(description="미실현 손익")
    cumulative_return: float = Field(description="누적 수익률 (%)")
    
    # 차트용 가격 히스토리
    price_history: List[Dict[str, Any]] = Field(description="가격 히스토리")

# ================================
# RISK & ALLOCATION SCHEMAS
# ================================

class RiskMetricsResponse(BaseModel):
    """리스크 지표"""
    volatility: Optional[float] = Field(None, description="변동성 (%)")
    max_drawdown: Optional[float] = Field(None, description="최대 낙폭 (%)")
    beta: Optional[float] = Field(None, description="베타")
    sharpe_ratio: Optional[float] = Field(None, description="샤프 비율")
    var_95: Optional[float] = Field(None, description="95% VaR")
    tracking_error: Optional[float] = Field(None, description="추적 오차 (%)")
    as_of_date: date = Field(description="기준일")

class AllocationResponse(BaseModel):
    """배분 현황 (섹터/자산클래스별)"""
    category: str = Field(description="카테고리명 (섹터/자산클래스)")
    weight: float = Field(description="비중 (%)")
    value: float = Field(description="시장가치")

class RiskAndAllocationResponse(BaseModel):
    """리스크 및 배분 현황 응답"""
    risk_metrics: Optional[RiskMetricsResponse] = None
    sector_allocation: List[AllocationResponse] = Field(description="섹터별 배분")
    asset_class_allocation: Optional[List[AllocationResponse]] = Field(None, description="자산클래스별 배분")
    period: TimePeriod
    start_date: date
    end_date: date

# ================================
# ERROR RESPONSES
# ================================

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str = Field(description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
    code: Optional[str] = Field(None, description="에러 코드")

# ================================
# LEGACY COMPATIBILITY
# ================================

# 기존 코드와의 호환성을 위한 별칭들
PortfolioResponse = PortfolioSummaryResponse
AssetResponse = AssetHoldingResponse
PerformanceData = PerformanceDataPoint

# TypeScript 프론트엔드와의 호환성을 위한 변환 헬퍼
def to_frontend_format(data: BaseModel) -> dict:
    """
    백엔드 응답을 프론트엔드 형식으로 변환
    (snake_case -> camelCase 변환 등)
    """
    result = data.model_dump()
    
    # snake_case to camelCase 변환
    def snake_to_camel(snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    camel_result = {}
    for key, value in result.items():
        camel_key = snake_to_camel(key)
        camel_result[camel_key] = value
        # 원본 키도 유지 (호환성)
        camel_result[key] = value
    
    return camel_result

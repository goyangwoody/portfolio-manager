"""
Risk analysis schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as Date

from .common import AssetFilter, TimePeriod

# ================================
# RISK ANALYSIS SCHEMAS
# ================================

class PortfolioRiskMetrics(BaseModel):
    """포트폴리오 리스크 지표"""
    volatility: float = Field(description="변동성 (연환산, %)")
    sharpe_ratio: float = Field(description="샤프 비율")
    max_drawdown: float = Field(description="최대 낙폭 (%)")
    var_95: float = Field(description="95% VaR (%)")
    var_99: float = Field(description="99% VaR (%)")
    
    # 기간 정보
    period_days: int = Field(description="분석 기간 (일)")
    start_date: Date = Field(description="분석 시작일")
    end_date: Date = Field(description="분석 종료일")

class AssetRiskContribution(BaseModel):
    """개별 자산 리스크 기여도"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    
    # 현재 포지션
    current_weight: float = Field(description="현재 비중 (%)")
    
    # 리스크 지표
    volatility: float = Field(description="개별 변동성 (%)")
    beta: Optional[float] = Field(None, description="베타 (vs 포트폴리오)")
    
    # 리스크 기여도
    risk_contribution: float = Field(description="포트폴리오 리스크 기여도 (%)")
    marginal_var: float = Field(description="한계 VaR")
    
    class Config:
        from_attributes = True

class RiskAnalysisResponse(BaseModel):
    """리스크 분석 응답"""
    # 포트폴리오 전체 리스크
    portfolio_metrics: PortfolioRiskMetrics = Field(description="포트폴리오 리스크 지표")
    
    # 자산별 리스크 기여도
    asset_risk_contributions: List[AssetRiskContribution] = Field(description="자산별 리스크 기여도")
    
    # 상위 리스크 기여 자산
    top_risk_contributors: List[AssetRiskContribution] = Field(description="상위 리스크 기여 자산")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")
    
    # 분석 조건
    period: TimePeriod = Field(description="분석 기간")
    confidence_level: float = Field(default=0.95, description="신뢰수준")
    
    # 검증용
    total_risk_contribution_check: Optional[float] = Field(None, description="총 리스크 기여도 합계 검증값")

# ================================
# CORRELATION ANALYSIS SCHEMAS
# ================================

class AssetCorrelation(BaseModel):
    """자산간 상관관계"""
    asset1_id: int
    asset1_ticker: str
    asset2_id: int  
    asset2_ticker: str
    correlation: float = Field(description="상관계수", ge=-1.0, le=1.0)

class CorrelationMatrix(BaseModel):
    """상관관계 매트릭스"""
    asset_correlations: List[AssetCorrelation] = Field(description="자산간 상관관계 목록")
    
    # 기간 정보
    period: TimePeriod = Field(description="분석 기간")
    start_date: Date = Field(description="분석 시작일")
    end_date: Date = Field(description="분석 종료일")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")

# ================================
# STRESS TESTING SCHEMAS
# ================================

class StressScenario(BaseModel):
    """스트레스 시나리오"""
    scenario_name: str = Field(description="시나리오명")
    description: str = Field(description="시나리오 설명")
    
    # 시나리오 충격
    market_shock: float = Field(description="시장 충격 (%)")
    sector_shocks: Optional[dict] = Field(None, description="섹터별 충격")
    
class StressTestResult(BaseModel):
    """스트레스 테스트 결과"""
    scenario: StressScenario = Field(description="적용된 시나리오")
    
    # 포트폴리오 영향
    portfolio_impact: float = Field(description="포트폴리오 영향 (%)")
    value_at_risk: float = Field(description="위험가치")
    
    # 자산별 영향
    asset_impacts: List[dict] = Field(description="자산별 영향")
    
class StressTestResponse(BaseModel):
    """스트레스 테스트 응답"""
    stress_results: List[StressTestResult] = Field(description="스트레스 테스트 결과 목록")
    
    # 기준 정보
    base_portfolio_value: float = Field(description="기준 포트폴리오 가치")
    as_of_date: Date = Field(description="기준일")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")

# ================================
# ASSET ALLOCATION SCHEMAS
# ================================

class AssetAllocationItem(BaseModel):
    """자산 배분 항목"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    market_value: float = Field(description="시장가치")
    weight: float = Field(description="비중 (%)")
    
    class Config:
        from_attributes = True

class AssetClassAllocation(BaseModel):
    """자산군별 배분"""
    asset_class: str = Field(description="자산군")
    total_value: float = Field(description="총 시장가치")
    total_weight: float = Field(description="총 비중 (%)")
    asset_count: int = Field(description="자산 수")
    assets: List[AssetAllocationItem] = Field(description="구성 자산 목록")

class AssetAllocationResponse(BaseModel):
    """자산 배분 응답"""
    total_portfolio_value: float = Field(description="포트폴리오 총 가치")
    as_of_date: Date = Field(description="기준일")
    allocations: List[AssetClassAllocation] = Field(description="자산군별 배분")
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")

# ================================
# ASSET CLASS DETAIL SCHEMAS
# ================================

class AssetClassDetailItem(BaseModel):
    """자산군 상세 - 개별 자산 정보"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    
    # 포지션 정보
    quantity: float = Field(description="보유 수량")
    avg_price: float = Field(description="평균 매입가")
    current_price: float = Field(description="현재가")
    market_value: float = Field(description="시장가치")
    weight: float = Field(description="포트폴리오 내 비중 (%)")
    
    # 수익률 정보
    day_change: Optional[float] = Field(None, description="일간 변동")
    day_change_percent: Optional[float] = Field(None, description="일간 변동률 (%)")
    unrealized_pnl: Optional[float] = Field(None, description="미실현 손익")
    total_return_percent: Optional[float] = Field(None, description="총 수익률 (%)")
    
    # 메타데이터
    region: Optional[str] = Field(None, description="지역")
    currency: Optional[str] = Field(None, description="통화")
    
    class Config:
        from_attributes = True

class AssetClassDetailsResponse(BaseModel):
    """자산군 상세 정보 응답"""
    asset_class: str = Field(description="자산군명")
    total_value: float = Field(description="총 시장가치")
    total_weight: float = Field(description="포트폴리오 내 총 비중 (%)")
    asset_count: int = Field(description="자산 수")
    
    # 자산 목록
    assets: List[AssetClassDetailItem] = Field(description="구성 자산 상세 목록")
    
    # 기준 정보
    as_of_date: Date = Field(description="기준일")
    portfolio_id: int = Field(description="포트폴리오 ID")
    
    # 통계 정보
    avg_return: Optional[float] = Field(None, description="평균 수익률 (%)")
    total_unrealized_pnl: Optional[float] = Field(None, description="총 미실현 손익")
    
# ================================
# LEGACY RISK SCHEMAS
# ================================

class VolatilityResponse(BaseModel):
    """변동성 분석 응답 (레거시)"""
    portfolio_volatility: float = Field(description="포트폴리오 변동성 (%)")
    period: TimePeriod
    start_date: Date
    end_date: Date

class RiskContributionResponse(BaseModel):
    """리스크 기여도 응답 (레거시)"""
    asset_id: int
    ticker: str
    name: str
    risk_contribution: float = Field(description="리스크 기여도 (%)")
    
    class Config:
        from_attributes = True

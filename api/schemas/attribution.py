"""
Attribution analysis schemas (TWR-based)
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from .common import AssetFilter, TimePeriod

# ================================
# ATTRIBUTION SCHEMAS (TWR 기반)
# ================================

class DailyPortfolioReturn(BaseModel):
    """일별 포트폴리오 수익률"""
    date: date
    daily_return: float = Field(description="일별 포트폴리오 수익률 (%)")
    portfolio_value: Optional[float] = Field(None, description="포트폴리오 가치 (선택적)")

class AssetWeightTrend(BaseModel):
    """자산별 비중 변화 추이"""
    date: date
    weight: float = Field(description="자산 비중 (%)")

class AssetReturnTrend(BaseModel):
    """자산별 TWR 수익률 추이"""
    date: date
    cumulative_twr: float = Field(description="누적 TWR 수익률 (%)")
    daily_twr: float = Field(description="일별 TWR 수익률 (%)")

class PricePerformancePoint(BaseModel):
    """개별 자산 가격 성과 데이터"""
    date: date
    performance: float = Field(description="정규화된 성과 (기준일=0%)")

class AssetContribution(BaseModel):
    """개별 자산 기여도 (TWR 기반)"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    region: Optional[str] = Field(None, description="domestic/foreign")
    
    # 현재 상태
    current_allocation: Optional[float] = Field(None, description="현재 비중 (%)")
    current_price: Optional[float] = Field(None, description="현재가")
    
    # 기간별 통계
    avg_weight: float = Field(description="평균 비중 (%)")
    period_return: float = Field(description="자산 기간 TWR 수익률 (%)")
    contribution: float = Field(description="포트폴리오 수익률 기여도 (%)")
    
    # 상세 데이터 (드릴다운용)
    weight_trend: Optional[List[AssetWeightTrend]] = Field(None, description="비중 변화 추이")
    return_trend: Optional[List[AssetReturnTrend]] = Field(None, description="TWR 수익률 추이")
    
    class Config:
        from_attributes = True

class AssetClassContribution(BaseModel):
    """자산클래스별 기여도 (TWR 기반)"""
    asset_class: str = Field(description="자산 클래스명")
    
    # 현재 상태  
    current_allocation: Optional[float] = Field(None, description="현재 비중 (%)")
    
    # 기간별 통계
    avg_weight: float = Field(description="평균 비중 (%)")
    contribution: float = Field(description="포트폴리오 수익률 기여도 (%)")
    
    # 차트 데이터
    weight_trend: Optional[List[AssetWeightTrend]] = Field(None, description="자산클래스 비중 변화 추이")
    return_trend: Optional[List[AssetReturnTrend]] = Field(None, description="자산클래스 TWR 수익률 추이")
    
    # 구성 자산들
    assets: Optional[List[AssetContribution]] = Field(None, description="자산클래스 내 자산들")
    
    class Config:
        from_attributes = True

class AssetDetailResponse(BaseModel):
    """개별 자산 상세 정보 (드릴다운용)"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    region: str
    
    # 현재 포지션 정보
    current_allocation: float = Field(description="현재 비중 (%)")
    current_price: float = Field(description="현재가")
    nav_return: float = Field(description="NAV 수익률 (%)")
    twr_contribution: float = Field(description="TWR 기여도 (%)")
    
    # 차트 데이터
    price_performance: List[PricePerformancePoint] = Field(description="가격 성과 차트")
    
    class Config:
        from_attributes = True

class AttributionAllTimeResponse(BaseModel):
    """All Time 기여도 분석 응답"""
    # 포트폴리오 전체 성과
    total_twr: float = Field(description="총 TWR 수익률 (%)")
    daily_returns: List[DailyPortfolioReturn] = Field(description="일별 포트폴리오 수익률")
    
    # 자산클래스별 기여도 (차트 데이터 포함)
    asset_class_contributions: List[AssetClassContribution] = Field(description="자산클래스별 기여도")
    
    # 상위/하위 기여 자산
    top_contributors: List[AssetContribution] = Field(description="상위 기여 자산")
    top_detractors: List[AssetContribution] = Field(description="상위 손실 자산")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")
    
    # 기간 정보
    period: TimePeriod
    start_date: date
    end_date: date
    
    # 검증용 (디버깅)
    total_contribution_check: Optional[float] = Field(None, description="총 기여도 합계 검증값")

class AttributionSpecificPeriodResponse(BaseModel):
    """Specific Period 기여도 분석 응답"""
    # 포트폴리오 전체 성과
    period_twr: float = Field(description="기간 TWR 수익률 (%)")
    daily_returns: List[DailyPortfolioReturn] = Field(description="기간 중 일별 포트폴리오 수익률")
    
    # 자산클래스별 기여도 (기간 중)
    asset_class_contributions: List[AssetClassContribution] = Field(description="기간 중 자산클래스별 기여도")
    
    # 상위/하위 기여 자산 (기간 중)
    top_contributors: List[AssetContribution] = Field(description="기간 중 상위 기여 자산")
    top_detractors: List[AssetContribution] = Field(description="기간 중 상위 손실 자산")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")
    
    # 기간 정보
    start_date: date = Field(description="분석 시작일")
    end_date: date = Field(description="분석 종료일")
    period_type: str = Field(description="기간 타입 (week/month/custom)")
    
    # 검증용
    total_contribution_check: Optional[float] = Field(None, description="총 기여도 합계 검증값")

class AttributionCustomPeriodResponse(BaseModel):
    """Custom Period 기여도 분석 응답 (레거시)"""
    # 포트폴리오 전체 성과
    period_twr: float = Field(description="기간 TWR 수익률 (%)")
    daily_returns: List[DailyPortfolioReturn] = Field(description="기간 중 일별 포트폴리오 수익률")
    
    # 자산클래스별 기여도
    asset_class_contributions: List[AssetClassContribution] = Field(description="자산클래스별 기여도")
    
    # 상위/하위 기여 자산
    top_contributors: List[AssetContribution] = Field(description="상위 기여 자산 (top 5)")
    top_detractors: List[AssetContribution] = Field(description="상위 손실 자산 (top 5)")
    
    # 기간 정보
    start_date: date = Field(description="분석 시작일")
    end_date: date = Field(description="분석 종료일")
    period_type: str = Field(description="기간 타입 (week/month)")
    
    # 검증용
    total_contribution_check: Optional[float] = Field(None, description="총 기여도 합계 검증값")

# ================================
# LEGACY ATTRIBUTION SCHEMAS (REMOVED)
# ================================
# Legacy schemas have been removed to use only TWR-based attribution
# Old endpoints: /attribution (removed)
# New endpoints: /attribution/all-time, /attribution/specific-period

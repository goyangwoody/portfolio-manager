"""
Holdings and positions schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as Date

from .common import AssetFilter

# ================================
# HOLDINGS SCHEMAS
# ================================

class HoldingBase(BaseModel):
    """홀딩 기본 정보"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    region: Optional[str] = Field(None, description="domestic/foreign")

class CurrentHolding(HoldingBase):
    """현재 보유 자산"""
    quantity: float = Field(description="수량")
    unit_price: float = Field(description="단가")
    market_value: float = Field(description="시장가치")
    average_cost: float = Field(description="평균단가")
    unrealized_pnl: float = Field(description="미실현 손익")
    unrealized_pnl_pct: float = Field(description="미실현 손익률 (%)")
    weight: float = Field(description="포트폴리오 비중 (%)")
    
    class Config:
        from_attributes = True

class PositionSnapshot(HoldingBase):
    """특정 시점 포지션 스냅샷"""
    date: Date = Field(description="스냅샷 날짜")
    quantity: float = Field(description="수량")
    unit_price: float = Field(description="단가")
    market_value: float = Field(description="시장가치")
    weight: float = Field(description="포트폴리오 비중 (%)")
    
    class Config:
        from_attributes = True

class HoldingsResponse(BaseModel):
    """현재 홀딩 조회 응답"""
    holdings: List[CurrentHolding] = Field(description="현재 보유 자산 목록")
    total_market_value: float = Field(description="총 시장가치")
    total_cost: float = Field(description="총 취득원가")
    total_unrealized_pnl: float = Field(description="총 미실현 손익")
    total_unrealized_pnl_pct: float = Field(description="총 미실현 손익률 (%)")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")
    as_of_date: Date = Field(description="기준일")

class PositionsResponse(BaseModel):
    """특정 시점 포지션 조회 응답"""
    positions: List[PositionSnapshot] = Field(description="포지션 스냅샷 목록")
    total_market_value: float = Field(description="총 시장가치")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")
    snapshot_date: Date = Field(description="스냅샷 기준일")

# ================================
# ASSET ALLOCATION SCHEMAS
# ================================

class AssetClassAllocation(BaseModel):
    """자산클래스별 배분"""
    asset_class: str = Field(description="자산 클래스명")
    market_value: float = Field(description="시장가치")
    weight: float = Field(description="비중 (%)")
    count: int = Field(description="자산 개수")

class RegionAllocation(BaseModel):
    """지역별 배분"""
    region: str = Field(description="지역 (domestic/foreign)")
    market_value: float = Field(description="시장가치")
    weight: float = Field(description="비중 (%)")
    count: int = Field(description="자산 개수")

class AllocationResponse(BaseModel):
    """자산 배분 현황 응답"""
    asset_class_allocation: List[AssetClassAllocation] = Field(description="자산클래스별 배분")
    region_allocation: List[RegionAllocation] = Field(description="지역별 배분")
    
    total_market_value: float = Field(description="총 시장가치")
    as_of_date: Date = Field(description="기준일")
    
    # 필터 정보
    asset_filter: AssetFilter = Field(description="적용된 자산 필터")

# ================================
# LEGACY HOLDINGS SCHEMAS
# ================================

class AssetHolding(BaseModel):
    """개별 자산 보유 현황 (레거시)"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    quantity: float = Field(description="수량")
    unit_price: float = Field(description="단가")
    market_value: float = Field(description="시장가치")
    weight: float = Field(description="포트폴리오 비중 (%)")
    
    class Config:
        from_attributes = True

class PortfolioHoldingsResponse(BaseModel):
    """포트폴리오 홀딩 응답 (레거시)"""
    holdings: List[AssetHolding] = Field(description="보유 자산 목록")
    total_value: float = Field(description="총 가치")
    as_of_date: Date = Field(description="기준일")

"""
Asset information and details schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as Date

# ================================
# ASSET INFO SCHEMAS  
# ================================

class AssetInfo(BaseModel):
    """자산 기본 정보"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    region: Optional[str] = Field(None, description="domestic/foreign")
    currency: Optional[str] = Field(None, description="자산 통화")
    
    class Config:
        from_attributes = True

class AssetDetail(AssetInfo):
    """자산 상세 정보"""
    # 현재 가격 정보
    current_price: Optional[float] = Field(None, description="현재가")
    price_date: Optional[Date] = Field(None, description="가격 기준일")
    
    # 메타데이터
    inception_date: Optional[Date] = Field(None, description="설정일")
    expense_ratio: Optional[float] = Field(None, description="운용보수 (%)")
    
    # 기타 정보
    isin: Optional[str] = Field(None, description="ISIN 코드")
    sedol: Optional[str] = Field(None, description="SEDOL 코드")
    
    class Config:
        from_attributes = True

class PriceHistory(BaseModel):
    """가격 히스토리"""
    date: Date
    price: float
    
class AssetPriceResponse(BaseModel):
    """자산 가격 조회 응답"""
    asset_info: AssetInfo = Field(description="자산 기본 정보")
    price_history: List[PriceHistory] = Field(description="가격 히스토리")
    
    # 기간 정보
    start_date: Date = Field(description="조회 시작일")
    end_date: Date = Field(description="조회 종료일")

class AssetsListResponse(BaseModel):
    """자산 목록 조회 응답"""
    assets: List[AssetInfo] = Field(description="자산 목록")
    total_count: int = Field(description="총 자산 수")
    
    # 필터 정보 (옵션)
    filtered_by_class: Optional[str] = Field(None, description="필터된 자산클래스")
    filtered_by_region: Optional[str] = Field(None, description="필터된 지역")

# ================================
# ASSET SEARCH SCHEMAS
# ================================

class AssetSearchCriteria(BaseModel):
    """자산 검색 조건"""
    keyword: Optional[str] = Field(None, description="키워드 (ticker, name)")
    asset_class: Optional[str] = Field(None, description="자산클래스")
    region: Optional[str] = Field(None, description="지역")
    currency: Optional[str] = Field(None, description="통화")

class AssetSearchResponse(BaseModel):
    """자산 검색 응답"""
    assets: List[AssetDetail] = Field(description="검색된 자산 목록")
    search_criteria: AssetSearchCriteria = Field(description="검색 조건")
    result_count: int = Field(description="검색 결과 수")

# ================================
# BENCHMARK SCHEMAS
# ================================

class BenchmarkInfo(BaseModel):
    """벤치마크 정보"""
    benchmark_id: int
    name: str
    ticker: str
    asset_class: str
    description: Optional[str] = Field(None, description="벤치마크 설명")
    
    class Config:
        from_attributes = True

class BenchmarkPerformance(BaseModel):
    """벤치마크 성과"""
    benchmark_info: BenchmarkInfo = Field(description="벤치마크 정보")
    period_return: float = Field(description="기간 수익률 (%)")
    annualized_return: Optional[float] = Field(None, description="연환산 수익률 (%)")
    volatility: Optional[float] = Field(None, description="변동성 (%)")
    
    # 기간 정보
    start_date: Date = Field(description="분석 시작일")
    end_date: Date = Field(description="분석 종료일")

class BenchmarkComparisonResponse(BaseModel):
    """벤치마크 비교 응답"""
    portfolio_return: float = Field(description="포트폴리오 수익률 (%)")
    benchmark_performances: List[BenchmarkPerformance] = Field(description="벤치마크 성과 목록")
    
    # 기간 정보
    start_date: Date = Field(description="분석 시작일") 
    end_date: Date = Field(description="분석 종료일")

# ================================
# LEGACY ASSET SCHEMAS
# ================================

class Asset(BaseModel):
    """자산 정보 (레거시)"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    
    class Config:
        from_attributes = True

from decimal import Decimal
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """기본 응답 스키마"""
    success: bool = True
    message: str = "Success"


class PortfolioPositionDailyBase(BaseModel):
    """일별 포트폴리오 포지션 기본 스키마"""
    portfolio_id: int = Field(..., description="포트폴리오 ID")
    as_of_date: date = Field(..., description="기준 날짜")
    asset_id: int = Field(..., description="자산 ID")
    quantity: Decimal = Field(..., description="보유 수량")
    avg_price: Decimal = Field(..., description="평균 매입 단가")
    market_value: Decimal = Field(..., description="시장 가치")


class PortfolioPositionDailyDetail(PortfolioPositionDailyBase):
    """자산 정보가 포함된 일별 포지션 상세 스키마"""
    asset_name: str = Field(..., description="자산명")
    asset_symbol: str = Field(..., description="자산 심볼")
    asset_class: str = Field(..., description="자산 클래스")
    current_price: Optional[Decimal] = Field(None, description="현재 가격")
    day_change: Optional[Decimal] = Field(None, description="일일 변동액")
    day_change_percent: Optional[Decimal] = Field(None, description="일일 변동률")
    weight: Optional[Decimal] = Field(None, description="포트폴리오 내 비중")


class PortfolioPositionsByDate(BaseModel):
    """날짜별 포지션 그룹"""
    as_of_date: date = Field(..., description="기준 날짜")
    positions: List[PortfolioPositionDailyDetail] = Field(..., description="해당 날짜의 포지션 목록")
    total_market_value: Decimal = Field(..., description="총 시장 가치")
    asset_count: int = Field(..., description="보유 자산 수")


class PortfolioPositionsHistoryResponse(BaseResponse):
    """포트폴리오 포지션 히스토리 응답"""
    data: List[PortfolioPositionsByDate] = Field(..., description="날짜별 포지션 목록")
    date_range: dict = Field(..., description="조회된 날짜 범위")
    total_dates: int = Field(..., description="총 날짜 수")


class PortfolioPositionDailyCreate(PortfolioPositionDailyBase):
    """일별 포지션 생성용 스키마"""
    pass


class PortfolioPositionDailyUpdate(BaseModel):
    """일별 포지션 업데이트용 스키마"""
    quantity: Optional[Decimal] = None
    avg_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None

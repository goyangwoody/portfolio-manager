from datetime import date
from typing import List
from pydantic import BaseModel
from decimal import Decimal


class AssetPriceData(BaseModel):
    """자산 가격 데이터"""
    date: date
    price: Decimal
    
    class Config:
        from_attributes = True


class AssetPriceHistoryResponse(BaseModel):
    """자산 가격 히스토리 응답"""
    asset_id: int
    asset_name: str
    asset_symbol: str
    prices: List[AssetPriceData]
    
    class Config:
        from_attributes = True

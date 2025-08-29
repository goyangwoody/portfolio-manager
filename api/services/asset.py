from datetime import date, timedelta
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

# models.py에서 필요한 모델들 import
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pm.db.models import Asset, Price

from schemas.asset import AssetPriceHistoryResponse, AssetPriceData


class AssetService:
    """자산 관련 비즈니스 로직"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_asset_price_history(
        self,
        asset_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: int = 30
    ) -> AssetPriceHistoryResponse:
        """
        자산의 가격 히스토리 조회
        
        Args:
            asset_id: 자산 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
            days: 조회할 일수 (start_date가 없을 때 사용)
            
        Returns:
            자산 가격 히스토리
        """
        try:
            # 자산 정보 조회
            asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")
            
            # 날짜 범위 설정
            if not end_date:
                end_date = date.today()
            
            if not start_date:
                start_date = end_date - timedelta(days=days)
            
            print(f"🔍 Getting price history for asset {asset_id} from {start_date} to {end_date}")
            
            # 가격 데이터 조회
            prices_query = (
                self.db.query(Price)
                .filter(
                    and_(
                        Price.asset_id == asset_id,
                        Price.date >= start_date,
                        Price.date <= end_date
                    )
                )
                .order_by(Price.date)
            )
            
            price_records = prices_query.all()
            print(f"📊 Found {len(price_records)} price records")
            
            # 가격 데이터 변환
            price_data = [
                AssetPriceData(
                    date=record.date,
                    price=record.close  # close 필드를 price로 사용
                )
                for record in price_records
            ]
            
            return AssetPriceHistoryResponse(
                asset_id=asset.id,
                asset_name=asset.name,
                asset_symbol=asset.ticker,  # ticker를 symbol로 사용
                prices=price_data
            )
            
        except Exception as e:
            print(f"❌ Error getting price history for asset {asset_id}: {e}")
            raise

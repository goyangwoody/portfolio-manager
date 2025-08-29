from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func

# models.py에서 필요한 모델들 import
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pm.db.models import PortfolioPositionDaily, Asset, Price

from schemas.position import (
    PortfolioPositionsByDate, 
    PortfolioPositionDailyDetail,
    PortfolioPositionsHistoryResponse
)


class PositionService:
    """포트폴리오 포지션 관련 비즈니스 로직"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_latest_position_date(self, portfolio_id: int) -> Optional[date]:
        """
        포트폴리오의 가장 최근 포지션 날짜 조회
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            가장 최근 포지션 날짜
        """
        try:
            latest_date = (
                self.db.query(PortfolioPositionDaily.as_of_date)
                .filter(PortfolioPositionDaily.portfolio_id == portfolio_id)
                .order_by(desc(PortfolioPositionDaily.as_of_date))
                .first()
            )
            
            return latest_date[0] if latest_date else None
        except Exception as e:
            print(f"❌ Error getting latest position date for portfolio {portfolio_id}: {e}")
            return None
    
    def get_portfolio_positions_by_date_range(
        self,
        portfolio_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30
    ) -> List[PortfolioPositionsByDate]:
        """
        날짜 범위별 포트폴리오 포지션 조회
        
        Args:
            portfolio_id: 포트폴리오 ID
            start_date: 시작 날짜 (None이면 최근 30일)
            end_date: 종료 날짜 (None이면 오늘)
            limit: 최대 조회 날짜 수
            
        Returns:
            날짜별 포지션 목록
        """
        try:
            print(f"🔍 Getting positions for portfolio {portfolio_id}, dates: {start_date} to {end_date}")
            
            # 기본 날짜 설정
            if end_date is None:
                end_date = date.today()
            if start_date is None:
                start_date = end_date - timedelta(days=limit)
            
            print(f"📅 Final date range: {start_date} to {end_date}")
            
            # ORM 쿼리: 포지션 데이터와 자산 정보 조인
            query = (
                self.db.query(
                    PortfolioPositionDaily.as_of_date,
                    PortfolioPositionDaily.asset_id,
                    PortfolioPositionDaily.quantity,
                    PortfolioPositionDaily.avg_price,
                    PortfolioPositionDaily.market_value,
                    Asset.name.label('asset_name'),
                    Asset.ticker.label('asset_symbol'),  # symbol -> ticker
                    Asset.asset_class,
                    func.coalesce(Price.close, PortfolioPositionDaily.avg_price).label('current_price')
                )
                .join(Asset, PortfolioPositionDaily.asset_id == Asset.id)
                .outerjoin(Price, and_(
                    Asset.id == Price.asset_id,
                    Price.date == PortfolioPositionDaily.as_of_date
                ))
                .filter(
                    PortfolioPositionDaily.portfolio_id == portfolio_id,
                    PortfolioPositionDaily.as_of_date.between(start_date, end_date),
                    PortfolioPositionDaily.quantity > 0
                )
                .order_by(desc(PortfolioPositionDaily.as_of_date), asc(Asset.name))
            )
            
            print(f"🔍 Executing query...")
            result = query.all()
            print(f"📊 Query returned {len(result)} rows")
            
            if not result:
                print(f"⚠️ No data found for portfolio {portfolio_id} in date range {start_date} to {end_date}")
                return []
                
        except Exception as e:
            print(f"❌ Error in ORM query: {e}")
            import traceback
            traceback.print_exc()
            raise e
        
        # 날짜별로 그룹화
        positions_by_date: Dict[date, List[Dict[str, Any]]] = {}
        
        for row in result:
            position_date = row.as_of_date
            if position_date not in positions_by_date:
                positions_by_date[position_date] = []
            
            # 일일 변동 계산 (기본값 0으로 설정)
            day_change = Decimal('0')
            day_change_percent = Decimal('0')
            if row.current_price and row.avg_price:
                day_change = (row.current_price - row.avg_price) * row.quantity
                if row.avg_price > 0:
                    day_change_percent = ((row.current_price - row.avg_price) / row.avg_price) * 100
            
            positions_by_date[position_date].append({
                'asset_id': row.asset_id,
                'quantity': row.quantity,
                'avg_price': row.avg_price,
                'market_value': row.market_value,
                'asset_name': row.asset_name,
                'asset_symbol': row.asset_symbol,
                'asset_class': row.asset_class,
                'current_price': row.current_price,
                'day_change': day_change,
                'day_change_percent': day_change_percent,
                'weight': None  # 포트폴리오 비중은 별도 계산
            })
        
        # 결과 구성
        result_list = []
        for position_date, positions in positions_by_date.items():
            # 해당 날짜의 총 시장 가치 계산
            total_market_value = sum(pos['market_value'] for pos in positions)
            
            # 각 포지션의 비중 계산
            for pos in positions:
                if total_market_value > 0:
                    pos['weight'] = (pos['market_value'] / total_market_value) * 100
            
            # PortfolioPositionDailyDetail 객체 생성
            position_details = []
            for pos in positions:
                try:
                    detail = PortfolioPositionDailyDetail(
                        portfolio_id=portfolio_id,
                        as_of_date=position_date,
                        asset_id=pos['asset_id'],
                        quantity=pos['quantity'],
                        avg_price=pos['avg_price'],
                        market_value=pos['market_value'],
                        asset_name=pos['asset_name'],
                        asset_symbol=pos['asset_symbol'],
                        asset_class=pos['asset_class'],
                        current_price=pos['current_price'],
                        day_change=pos['day_change'],
                        day_change_percent=pos['day_change_percent'],
                        weight=pos['weight']
                    )
                    position_details.append(detail)
                except Exception as e:
                    print(f"❌ Error creating PortfolioPositionDailyDetail: {e}")
                    print(f"   Position data: {pos}")
                    raise e
            
            try:
                result_list.append(PortfolioPositionsByDate(
                    as_of_date=position_date,
                    positions=position_details,
                    total_market_value=total_market_value,
                    asset_count=len(positions)
                ))
            except Exception as e:
                print(f"❌ Error creating PortfolioPositionsByDate: {e}")
                print(f"   Date: {position_date}, Assets: {len(positions)}, Total value: {total_market_value}")
                raise e
        
        return sorted(result_list, key=lambda x: x.as_of_date, reverse=True)
    
    def get_portfolio_positions_history(
        self,
        portfolio_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30
    ) -> PortfolioPositionsHistoryResponse:
        """
        포트폴리오 포지션 히스토리 조회
        """
        positions_by_date = self.get_portfolio_positions_by_date_range(
            portfolio_id, start_date, end_date, limit
        )
        
        # 날짜 범위 정보
        actual_start_date = min(p.as_of_date for p in positions_by_date) if positions_by_date else start_date
        actual_end_date = max(p.as_of_date for p in positions_by_date) if positions_by_date else end_date
        
        return PortfolioPositionsHistoryResponse(
            success=True,
            message="포트폴리오 포지션 히스토리 조회 성공",
            data=positions_by_date,
            date_range={
                'start_date': actual_start_date,
                'end_date': actual_end_date
            },
            total_dates=len(positions_by_date)
        )
    
    def get_latest_portfolio_positions(
        self,
        portfolio_id: int
    ) -> Optional[PortfolioPositionsByDate]:
        """
        최신 포트폴리오 포지션 조회
        """
        # 최신 날짜 조회 (ORM 방식)
        latest_date_result = (
            self.db.query(func.max(PortfolioPositionDaily.as_of_date))
            .filter(PortfolioPositionDaily.portfolio_id == portfolio_id)
            .scalar()
        )
        
        if not latest_date_result:
            return None
        
        latest_date = latest_date_result
        
        # 해당 날짜의 포지션 조회
        positions = self.get_portfolio_positions_by_date_range(
            portfolio_id, latest_date, latest_date, 1
        )
        
        return positions[0] if positions else None

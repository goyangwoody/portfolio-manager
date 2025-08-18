from datetime import date, timedelta
from decimal import Decimal
import pandas as pd
from sqlalchemy import select

from pm.db.models import (
    SessionLocal, Portfolio, Asset, PortfolioNavDaily,
    AssetAttributionPeriodic, AssetClassAttributionPeriodic, AttributionHighlightsPeriodic
)
from pm.data.utils.trading_calendar import TradingCalendar_KRX, TradingCalendar_NYSE
from scripts.attribution_visualization import period_attribution  # 기존 기여도 계산 함수 활용

class AttributionAnalyzer:
    """기여도 분석 결과 계산 및 DB 저장"""
    
    def __init__(self):
        pass
        
    def _compute_and_save_period_attribution(
        self,
        market: str,
        portfolio_name: str,
        period_type: str,
        start_date: date,
        end_date: date,
        period_ranges: list,
        top_n: int = 5
    ):
        """기간별 기여도 분석 수행 및 저장 (공통 로직)
        
        Args:
            portfolio_name: 포트폴리오 이름
            period_type: 분석 주기 ('WEEK', 'MONTH', 'QUARTER')
            start_date: 분석 시작일
            end_date: 분석 종료일
            period_ranges: 분석 기간 목록 [(start1, end1), (start2, end2), ...]
            top_n: Top/Bottom N 기여자 수
        """
        # Dynamically set the calendar based on the market
        if market.upper() == 'KRX':
            self.calendar = TradingCalendar_KRX()
        elif market.upper() == 'NYSE':
            self.calendar = TradingCalendar_NYSE()
        else:
            raise ValueError(f"Unsupported market: {market}")

        session = SessionLocal()
        try:
            # 1. 포트폴리오 ID 조회
            portfolio_id = session.execute(
                select(Portfolio.id).where(Portfolio.name == portfolio_name)
            ).scalar_one()
            
            for period_start, period_end in period_ranges:
                print(f"Processing {period_type.lower()}: {period_start} ~ {period_end}")
                
                # 2. 기여도 분석 수행
                asset_df, class_df = period_attribution(
                    portfolio_name=portfolio_name,
                    start_date=period_start,
                    end_date=period_end,
                    top_n=top_n
                )
                
                if asset_df.empty:
                    print(f"No data for period {period_start} ~ {period_end}")
                    continue
                
                # 3. 자산별 기여도 저장
                self._save_asset_attribution(
                    session, portfolio_id, period_type, 
                    period_start, period_end, asset_df
                )
                
                # 4. 자산군별 기여도 저장
                self._save_class_attribution(
                    session, portfolio_id, period_type,
                    period_start, period_end, class_df
                )
                
                # 5. Top/Bottom 기여자 저장
                self._save_attribution_highlights(
                    session, portfolio_id, period_type,
                    period_start, period_end, asset_df, top_n
                )
                
                session.commit()
                
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def compute_and_save_weekly_attribution(
        self,
        market: str,
        portfolio_name: str,
        start_date: date,
        end_date: date,
        top_n: int = 5
    ):
        """주간 기여도 분석 수행 및 저장"""
        # Dynamically set the calendar based on the market
        if market.upper() == 'KRX':
            self.calendar = TradingCalendar_KRX()
        elif market.upper() == 'NYSE':
            self.calendar = TradingCalendar_NYSE()
        else:
            raise ValueError(f"Unsupported market: {market}")

        week_ranges = self.calendar.get_week_ranges(start_date, end_date)
        self._compute_and_save_period_attribution(
            market=market,
            portfolio_name=portfolio_name,
            period_type='WEEK',
            start_date=start_date,
            end_date=end_date,
            period_ranges=week_ranges,
            top_n=top_n
        )
    
    def compute_and_save_monthly_attribution(
        self,
        market: str,
        portfolio_name: str,
        start_date: date,
        end_date: date,
        top_n: int = 5
    ):
        """월간 기여도 분석 수행 및 저장"""
        # Dynamically set the calendar based on the market
        if market.upper() == 'KRX':
            self.calendar = TradingCalendar_KRX()
        elif market.upper() == 'NYSE':
            self.calendar = TradingCalendar_NYSE()
        else:
            raise ValueError(f"Unsupported market: {market}")

        month_ranges = self.calendar.get_month_ranges(start_date, end_date)
        self._compute_and_save_period_attribution(
            market=market,
            portfolio_name=portfolio_name,
            period_type='MONTH',
            start_date=start_date,
            end_date=end_date,
            period_ranges=month_ranges,
            top_n=top_n
        )
    
    def compute_and_save_quarterly_attribution(
        self,
        market: str,
        portfolio_name: str,
        start_date: date,
        end_date: date,
        top_n: int = 5
    ):
        """분기 기여도 분석 수행 및 저장"""
        # Dynamically set the calendar based on the market
        if market.upper() == 'KRX':
            self.calendar = TradingCalendar_KRX()
        elif market.upper() == 'NYSE':
            self.calendar = TradingCalendar_NYSE()
        else:
            raise ValueError(f"Unsupported market: {market}")

        quarter_ranges = self.calendar.get_quarter_ranges(start_date, end_date)
        self._compute_and_save_period_attribution(
            market=market,
            portfolio_name=portfolio_name,
            period_type='QUARTER',
            start_date=start_date,
            end_date=end_date,
            period_ranges=quarter_ranges,
            top_n=top_n
        )
    
    def _save_asset_attribution(
        self, 
        session,
        portfolio_id: int,
        period_type: str,
        start_date: date,
        end_date: date,
        asset_df: pd.DataFrame
    ):
        """자산별 기여도 저장"""
        # 기존 데이터 삭제
        session.query(AssetAttributionPeriodic).filter(
            AssetAttributionPeriodic.portfolio_id == portfolio_id,
            AssetAttributionPeriodic.period_type == period_type,
            AssetAttributionPeriodic.start_date == start_date,
            AssetAttributionPeriodic.end_date == end_date
        ).delete()
        
        # 새 데이터 저장
        for _, row in asset_df.iterrows():
            record = AssetAttributionPeriodic(
                portfolio_id=portfolio_id,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                asset_id=row['asset_id'],
                start_nav=Decimal(str(row['market_value'])),
                end_nav=Decimal(str(row['market_value'] * (1 + row['return']))),
                avg_weight=Decimal(str(row['weight'])),
                total_return=Decimal(str(row['return'])),
                contribution=Decimal(str(row['contrib_pct'])),
                # selection/allocation은 현재 계산되지 않음
                selection_effect=Decimal('0'),
                allocation_effect=Decimal('0')
            )
            session.add(record)
    
    def _save_class_attribution(
        self,
        session,
        portfolio_id: int,
        period_type: str,
        start_date: date,
        end_date: date,
        class_df: pd.DataFrame
    ):
        """자산군별 기여도 저장"""
        # 기존 데이터 삭제
        session.query(AssetClassAttributionPeriodic).filter(
            AssetClassAttributionPeriodic.portfolio_id == portfolio_id,
            AssetClassAttributionPeriodic.period_type == period_type,
            AssetClassAttributionPeriodic.start_date == start_date,
            AssetClassAttributionPeriodic.end_date == end_date
        ).delete()
        
        # NAV 정보 가져오기
        nav = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == portfolio_id,
                PortfolioNavDaily.as_of_date == start_date
            )
        ).scalar_one()
        
        # 새 데이터 저장
        for _, row in class_df.iterrows():
            record = AssetClassAttributionPeriodic(
                portfolio_id=portfolio_id,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                asset_class=row['asset_class'],
                start_nav=Decimal(str(row['contrib_abs'] / row['contrib_pct'] if row['contrib_pct'] != 0 else 0)),
                end_nav=Decimal(str(row['contrib_abs'] / row['contrib_pct'] * (1 + row['contrib_pct']) if row['contrib_pct'] != 0 else 0)),
                avg_weight=Decimal(str(row['contrib_abs'] / nav if nav else 0)),
                total_return=Decimal(str(row['contrib_pct'])),
                contribution=Decimal(str(row['contrib_pct'])),
                selection_effect=Decimal('0'),
                allocation_effect=Decimal('0'),
                risk_contribution=Decimal('0'),
                tracking_error_contrib=Decimal('0')
            )
            session.add(record)
    
    def _save_attribution_highlights(
        self,
        session,
        portfolio_id: int,
        period_type: str,
        start_date: date,
        end_date: date,
        asset_df: pd.DataFrame,
        top_n: int
    ):
        """Top/Bottom 기여자 저장"""
        # 기존 데이터 삭제
        session.query(AttributionHighlightsPeriodic).filter(
            AttributionHighlightsPeriodic.portfolio_id == portfolio_id,
            AttributionHighlightsPeriodic.period_type == period_type,
            AttributionHighlightsPeriodic.start_date == start_date,
            AttributionHighlightsPeriodic.end_date == end_date
        ).delete()
        
        # Top/Bottom 기여자 추출 (이미 정렬되어 있음)
        top_assets = asset_df.head(top_n)
        bottom_assets = asset_df.tail(top_n).iloc[::-1]  # 역순으로
        
        # 저장
        for rank, row in top_assets.iterrows():
            record = AttributionHighlightsPeriodic(
                portfolio_id=portfolio_id,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                rank_type='TOP',
                rank_number=rank + 1,  # rank는 0부터 시작하므로 1을 더함
                asset_id=row['asset_id'],
                contribution=Decimal(str(row['contrib_pct'])),
                weight_avg=Decimal(str(row['weight'])),
                return_total=Decimal(str(row['return']))
            )
            session.add(record)
            
        for rank, row in bottom_assets.iterrows():
            record = AttributionHighlightsPeriodic(
                portfolio_id=portfolio_id,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                rank_type='BOTTOM',
                rank_number=rank + 1,  # rank는 0부터 시작하므로 1을 더함
                asset_id=row['asset_id'],
                contribution=Decimal(str(row['contrib_pct'])),
                weight_avg=Decimal(str(row['weight'])),
                return_total=Decimal(str(row['return']))
            )
            session.add(record)

if __name__ == '__main__':
    # 사용 예시
    analyzer = AttributionAnalyzer()
    analyzer.compute_and_save_weekly_attribution(
        market="NYSE",
        portfolio_name="USDCore",
        start_date=date(2025, 7,7),
        end_date=date(2025, 8, 15),
        top_n=5
    )

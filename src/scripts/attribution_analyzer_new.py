from datetime import date, timedelta
from decimal import Decimal
import pandas as pd
from sqlalchemy import select

from pm.db.models import SessionLocal, Portfolio, PortfolioNavDaily
from pm.data.utils.trading_calendar import TradingCalendar_KRX, TradingCalendar_NYSE
from scripts.attribution_visualization import period_attribution  # 기존 기여도 계산 함수 활용

class AttributionAnalyzer:
    """기여도 분석 계산 (DB 저장 없이 분석만 수행)"""
    
    def __init__(self):
        self.calendar = None
        
    def compute_period_attribution(
        self,
        market: str,
        portfolio_name: str,
        start_date: date,
        end_date: date,
        top_n: int = 5
    ):
        """단일 기간 기여도 분석 수행
        
        Args:
            market: 시장 ('KRX' or 'NYSE')
            portfolio_name: 포트폴리오 이름
            start_date: 분석 시작일
            end_date: 분석 종료일
            top_n: Top/Bottom N 기여자 수
            
        Returns:
            tuple: (asset_df, class_df) - 자산별, 자산군별 기여도 데이터프레임
        """
        # 시장별 캘린더 설정
        if market.upper() == 'KRX':
            self.calendar = TradingCalendar_KRX()
        elif market.upper() == 'NYSE':
            self.calendar = TradingCalendar_NYSE()
        else:
            raise ValueError(f"Unsupported market: {market}")

        print(f"Computing attribution for {portfolio_name}: {start_date} ~ {end_date}")
        
        # 기여도 분석 수행
        asset_df, class_df = period_attribution(
            portfolio_name=portfolio_name,
            start_date=start_date,
            end_date=end_date,
            top_n=top_n
        )
        
        return asset_df, class_df
    
    def compute_weekly_attribution(
        self,
        market: str,
        portfolio_name: str,
        start_date: date,
        end_date: date,
        top_n: int = 5
    ):
        """주간 기여도 분석
        
        Args:
            market: 시장 ('KRX' or 'NYSE')
            portfolio_name: 포트폴리오 이름
            start_date: 분석 시작일
            end_date: 분석 종료일
            top_n: Top/Bottom N 기여자 수
            
        Returns:
            list: [(period_start, period_end, asset_df, class_df), ...] 주간별 분석 결과
        """
        # 시장별 캘린더 설정
        if market.upper() == 'KRX':
            self.calendar = TradingCalendar_KRX()
        elif market.upper() == 'NYSE':
            self.calendar = TradingCalendar_NYSE()
        else:
            raise ValueError(f"Unsupported market: {market}")

        # 주간 기간 생성
        weekly_ranges = self.calendar.get_week_ranges(start_date, end_date)
        
        results = []
        for week_start, week_end in weekly_ranges:
            print(f"Processing week: {week_start} ~ {week_end}")
            asset_df, class_df = self.compute_period_attribution(
                market, portfolio_name, week_start, week_end, top_n
            )
            results.append((week_start, week_end, asset_df, class_df))
            
        return results
    
    def compute_monthly_attribution(
        self,
        market: str,
        portfolio_name: str,
        start_date: date,
        end_date: date,
        top_n: int = 5
    ):
        """월간 기여도 분석
        
        Args:
            market: 시장 ('KRX' or 'NYSE')
            portfolio_name: 포트폴리오 이름
            start_date: 분석 시작일
            end_date: 분석 종료일
            top_n: Top/Bottom N 기여자 수
            
        Returns:
            list: [(period_start, period_end, asset_df, class_df), ...] 월간별 분석 결과
        """
        # 시장별 캘린더 설정
        if market.upper() == 'KRX':
            self.calendar = TradingCalendar_KRX()
        elif market.upper() == 'NYSE':
            self.calendar = TradingCalendar_NYSE()
        else:
            raise ValueError(f"Unsupported market: {market}")

        # 월간 기간 생성
        monthly_ranges = self.calendar.get_month_ranges(start_date, end_date)
        
        results = []
        for month_start, month_end in monthly_ranges:
            print(f"Processing month: {month_start} ~ {month_end}")
            asset_df, class_df = self.compute_period_attribution(
                market, portfolio_name, month_start, month_end, top_n
            )
            results.append((month_start, month_end, asset_df, class_df))
            
        return results

    def get_top_contributors(self, asset_df: pd.DataFrame, n: int = 5):
        """Top N 기여자 반환"""
        if asset_df.empty:
            return pd.DataFrame()
        return asset_df.nlargest(n, 'contrib_pct')
    
    def get_bottom_contributors(self, asset_df: pd.DataFrame, n: int = 5):
        """Bottom N 기여자 반환"""
        if asset_df.empty:
            return pd.DataFrame()
        return asset_df.nsmallest(n, 'contrib_pct')


if __name__ == '__main__':
    # 사용 예시
    analyzer = AttributionAnalyzer()
    
    # 단일 기간 분석
    asset_df, class_df = analyzer.compute_period_attribution(
        market="KRX",
        portfolio_name="Core",
        start_date=date(2025, 7, 7),
        end_date=date(2025, 8, 15),
        top_n=5
    )
    
    print("=== 자산별 기여도 ===")
    print(asset_df.head())
    
    print("\n=== 자산군별 기여도 ===")
    print(class_df.head())
    
    print("\n=== Top 5 기여자 ===")
    print(analyzer.get_top_contributors(asset_df, 5))

    print("\n=== Bottom 5 기여자 ===")
    print(analyzer.get_bottom_contributors(asset_df, 5))
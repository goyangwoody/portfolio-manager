"""
Portfolio performance analysis services
"""
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database import get_db
from utils import safe_float, parse_custom_period
from schemas import (
    PerformanceAllTimeResponse, PerformanceCustomPeriodResponse,
    RecentReturnData, DailyReturnPoint, BenchmarkReturn, TimePeriod
)
from src.pm.db.models import PortfolioNavDaily, PortfolioPositionDaily

def parse_date_range(period: TimePeriod, portfolio_id: int, db: Session) -> tuple[date, date]:
    """기간 설정에 따른 시작일/종료일 계산"""
    # 최신 데이터 날짜 조회
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == portfolio_id
    ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
    
    if not latest_nav:
        raise ValueError("No data found for portfolio")
    
    end_date = latest_nav.as_of_date
    
    if period == TimePeriod.ALL or period == TimePeriod.INCEPTION:
        # 전체 기간: 가장 오래된 데이터부터
        oldest_nav = db.query(PortfolioNavDaily).filter(
            PortfolioNavDaily.portfolio_id == portfolio_id
        ).order_by(PortfolioNavDaily.as_of_date).first()
        start_date = oldest_nav.as_of_date if oldest_nav else end_date
    elif period == TimePeriod.YEAR_1:
        start_date = end_date - timedelta(days=365)
    elif period == TimePeriod.MONTH_6:
        start_date = end_date - timedelta(days=180)
    elif period == TimePeriod.MONTH_3:
        start_date = end_date - timedelta(days=90)
    elif period == TimePeriod.MONTH_1:
        start_date = end_date - timedelta(days=30)
    elif period == TimePeriod.WEEK_1:
        start_date = end_date - timedelta(days=7)
    else:
        # 기본값: 전체 기간
        oldest_nav = db.query(PortfolioNavDaily).filter(
            PortfolioNavDaily.portfolio_id == portfolio_id
        ).order_by(PortfolioNavDaily.as_of_date).first()
        start_date = oldest_nav.as_of_date if oldest_nav else end_date
    
    return start_date, end_date

async def get_performance_custom_period(
    portfolio_id: int, 
    custom_week: Optional[str], 
    custom_month: Optional[str], 
    db: Session
) -> PerformanceCustomPeriodResponse:
    """Custom Period 성과 데이터 조회"""
    
    # 커스텀 기간 파싱
    start_date, end_date, period_type = parse_custom_period(custom_week, custom_month)
    
    # 일별 수익률 계산을 위해 시작일 이전 데이터도 포함해서 조회
    extended_start_date = start_date - timedelta(days=7 if period_type == "week" else 10)
    
    # 확장된 기간으로 NAV 데이터 조회
    all_nav_data = db.query(PortfolioNavDaily).filter(
        and_(
            PortfolioNavDaily.portfolio_id == portfolio_id,
            PortfolioNavDaily.as_of_date >= extended_start_date,
            PortfolioNavDaily.as_of_date <= end_date
        )
    ).order_by(PortfolioNavDaily.as_of_date).all()
    
    # 실제 기간 내 데이터만 필터링
    nav_data = [nav for nav in all_nav_data if start_date <= nav.as_of_date <= end_date]
    
    if not nav_data:
        raise ValueError(f"No NAV data found for period {start_date} to {end_date}")
    
    # 1. 기간 누적 수익률 계산
    cumulative_return = calculate_cumulative_return_with_extended_data(all_nav_data, start_date, end_date)
    
    # 2. 기간 중 일별 수익률 계산
    daily_returns = calculate_period_daily_returns_with_extended_data(all_nav_data, start_date, end_date)
    
    # 3. 기간 중 벤치마크 대비 수익률 계산
    benchmark_returns = await calculate_benchmark_returns_custom_period(
        portfolio_id, start_date, end_date, cumulative_return, db
    )
    
    return PerformanceCustomPeriodResponse(
        cumulative_return=cumulative_return,
        daily_returns=daily_returns,
        benchmark_returns=benchmark_returns,
        start_date=start_date,
        end_date=end_date,
        period_type=period_type
    )

def calculate_cumulative_return_with_extended_data(all_nav_data: list, start_date: date, end_date: date) -> float:
    """확장된 데이터를 사용해서 기간 누적 수익률 계산 (전 영업일 대비)"""
    
    # 기간 내 데이터 필터링
    period_data = [nav for nav in all_nav_data if start_date <= nav.as_of_date <= end_date]
    if not period_data:
        return 0.0
    
    # 기간 시작 전 마지막 영업일 데이터 찾기
    pre_period_data = [nav for nav in all_nav_data if nav.as_of_date < start_date]
    if not pre_period_data:
        # 전 영업일 데이터가 없으면 기간 내 첫째 날과 마지막 날로 계산
        return calculate_cumulative_return(period_data)
    
    # 전 영업일 NAV와 기간 마지막 날 NAV로 계산
    start_nav = safe_float(pre_period_data[-1].nav)  # 기간 시작 전 마지막 영업일
    end_nav = safe_float(period_data[-1].nav)        # 기간 마지막 날
    
    if not start_nav or start_nav <= 0 or not end_nav:
        return 0.0
    
    cumulative_return = ((end_nav - start_nav) / start_nav) * 100
    return cumulative_return

def calculate_cumulative_return(nav_data: list) -> float:
    """기간 누적 수익률 계산"""
    if len(nav_data) < 2:
        return 0.0
    
    first_nav = safe_float(nav_data[0].nav)
    last_nav = safe_float(nav_data[-1].nav)
    
    if not first_nav or first_nav <= 0:
        return 0.0
    
    cumulative_return = ((last_nav - first_nav) / first_nav) * 100
    return cumulative_return

def calculate_period_daily_returns_with_extended_data(all_nav_data: list, start_date: date, end_date: date) -> list[DailyReturnPoint]:
    """확장된 데이터를 사용해서 기간 중 일별 수익률 계산 (전일 대비)"""
    if len(all_nav_data) < 2:
        return []
    
    daily_returns = []
    
    for i in range(1, len(all_nav_data)):
        curr_nav_record = all_nav_data[i]
        prev_nav_record = all_nav_data[i-1]
        
        # 현재 날짜가 타겟 기간 내에 있는지 확인
        if not (start_date <= curr_nav_record.as_of_date <= end_date):
            continue
            
        prev_nav = safe_float(prev_nav_record.nav)
        curr_nav = safe_float(curr_nav_record.nav)
        
        if prev_nav and prev_nav > 0 and curr_nav:
            daily_return = ((curr_nav - prev_nav) / prev_nav) * 100
            daily_returns.append(DailyReturnPoint(
                date=curr_nav_record.as_of_date,
                daily_return=daily_return,
                return_pct=daily_return
            ))
    
    return daily_returns

async def calculate_benchmark_returns_custom_period(
    portfolio_id: int, 
    start_date: date, 
    end_date: date, 
    portfolio_return: float,
    db: Session
) -> list[BenchmarkReturn]:
    """Custom Period 벤치마크 대비 수익률 계산"""
    
    # 현재는 실제 벤치마크 데이터가 없으므로 빈 리스트 반환
    # TODO: 실제 벤치마크 지수 데이터 연동 후 활성화
    return []

async def get_performance_all_time(portfolio_id: int, chart_period: str, db: Session) -> PerformanceAllTimeResponse:
    """All Time 성과 데이터 조회"""
    
    # 최신 NAV 데이터 조회
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == portfolio_id
    ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
    
    if not latest_nav:
        raise ValueError("No NAV data found")
    
    end_date = latest_nav.as_of_date
    
    # Recent Returns용 최근 30일 NAV 데이터 조회
    start_date_recent = end_date - timedelta(days=30)
    recent_nav_data = db.query(PortfolioNavDaily).filter(
        and_(
            PortfolioNavDaily.portfolio_id == portfolio_id,
            PortfolioNavDaily.as_of_date >= start_date_recent,
            PortfolioNavDaily.as_of_date <= end_date
        )
    ).order_by(PortfolioNavDaily.as_of_date).all()
    
    if not recent_nav_data:
        raise ValueError("No recent NAV data found")
    
    # 1. Recent Returns 계산 (1일/1주/1개월)
    recent_returns = calculate_recent_returns(recent_nav_data)
    
    # 2. 차트용 일별 수익률 데이터 (chart_period에 따라 기간 조정)
    chart_daily_returns = calculate_chart_daily_returns(portfolio_id, chart_period, end_date, db)
    
    # 3. 벤치마크 대비 수익률 (All Time)
    benchmark_returns = await calculate_benchmark_returns_all_time(portfolio_id, db)
    
    return PerformanceAllTimeResponse(
        recent_returns=recent_returns,
        recent_week_daily_returns=recent_returns.daily_returns or [],
        daily_returns=chart_daily_returns,
        benchmark_returns=benchmark_returns,
        start_date=recent_nav_data[0].as_of_date if recent_nav_data else end_date,
        end_date=end_date
    )

def calculate_recent_returns(nav_data: list) -> RecentReturnData:
    """최근 수익률 계산"""
    if len(nav_data) < 2:
        return RecentReturnData()
    
    # 최신 NAV
    latest_nav = safe_float(nav_data[-1].nav)
    
    # 1일 수익률
    day_1 = None
    if len(nav_data) >= 2:
        prev_nav = safe_float(nav_data[-2].nav)
        if prev_nav and prev_nav > 0 and latest_nav:
            day_1 = ((latest_nav - prev_nav) / prev_nav) * 100
    
    # 1주 수익률 (7일 전과 비교)
    week_1 = None
    if len(nav_data) >= 8:
        week_ago_nav = safe_float(nav_data[-8].nav)
        if week_ago_nav and week_ago_nav > 0 and latest_nav:
            week_1 = ((latest_nav - week_ago_nav) / week_ago_nav) * 100
    
    # 1개월 수익률 (30일 전과 비교, 또는 가장 오래된 데이터와 비교)
    month_1 = None
    if len(nav_data) >= 1:
        oldest_nav = safe_float(nav_data[0].nav)
        if oldest_nav and oldest_nav > 0 and latest_nav:
            month_1 = ((latest_nav - oldest_nav) / oldest_nav) * 100
    
    # 일별 수익률 (최근 7일)
    daily_returns = calculate_recent_week_daily_returns(nav_data)
    
    return RecentReturnData(
        daily_return=day_1,
        weekly_return=week_1,
        monthly_return=month_1,
        day_1=day_1,
        week_1=week_1,
        month_1=month_1,
        month_3=None,
        month_6=None,
        year_1=None,
        daily_returns=daily_returns
    )

def calculate_recent_week_daily_returns(nav_data: list) -> list[DailyReturnPoint]:
    """최근 주간 일별 수익률 계산"""
    if len(nav_data) < 2:
        return []
    
    # 최근 7일 또는 사용 가능한 데이터
    recent_data = nav_data[-8:] if len(nav_data) >= 8 else nav_data
    daily_returns = []
    
    for i in range(1, len(recent_data)):
        prev_nav = safe_float(recent_data[i-1].nav)
        curr_nav = safe_float(recent_data[i].nav)
        
        if prev_nav and prev_nav > 0 and curr_nav:
            daily_return = ((curr_nav - prev_nav) / prev_nav) * 100
            daily_returns.append(DailyReturnPoint(
                date=recent_data[i].as_of_date,
                daily_return=daily_return,
                return_pct=daily_return
            ))
    
    return daily_returns

def calculate_chart_daily_returns(portfolio_id: int, chart_period: str, end_date: date, db: Session) -> list[DailyReturnPoint]:
    """차트용 일별 수익률 계산 (기간별)"""
    
    # chart_period에 따라 시작일 결정
    if chart_period == "1w":
        start_date = end_date - timedelta(days=7)
    elif chart_period == "1m":
        start_date = end_date - timedelta(days=30)
    else:  # "all"
        # 전체 기간: 포트폴리오 시작부터 (최대 1년으로 제한)
        start_date = end_date - timedelta(days=365)
    
    # 수익률 계산을 위해 시작일보다 하루 더 일찍부터 조회
    extended_start_date = start_date - timedelta(days=1)
    
    # NAV 데이터 조회
    nav_data = db.query(PortfolioNavDaily).filter(
        and_(
            PortfolioNavDaily.portfolio_id == portfolio_id,
            PortfolioNavDaily.as_of_date >= extended_start_date,
            PortfolioNavDaily.as_of_date <= end_date
        )
    ).order_by(PortfolioNavDaily.as_of_date).all()
    
    if len(nav_data) < 2:
        return []
    
    daily_returns = []
    
    for i in range(1, len(nav_data)):
        curr_nav_record = nav_data[i]
        prev_nav_record = nav_data[i-1]
        
        # 타겟 기간 내의 데이터만 포함
        if curr_nav_record.as_of_date < start_date:
            continue
            
        prev_nav = safe_float(prev_nav_record.nav)
        curr_nav = safe_float(curr_nav_record.nav)
        
        if prev_nav and prev_nav > 0 and curr_nav:
            daily_return = ((curr_nav - prev_nav) / prev_nav) * 100
            daily_returns.append(DailyReturnPoint(
                date=curr_nav_record.as_of_date,
                daily_return=daily_return,
                return_pct=daily_return
            ))
    
    return daily_returns

async def calculate_benchmark_returns_all_time(portfolio_id: int, db: Session) -> list[BenchmarkReturn]:
    """All Time 벤치마크 대비 수익률 계산"""
    
    # 현재는 실제 벤치마크 데이터가 없으므로 빈 리스트 반환
    # TODO: 실제 벤치마크 지수 데이터 (KOSPI, KOSPI200, S&P500) 연동 후 활성화
    return []

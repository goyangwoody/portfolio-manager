import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

# 모델 import
from src.pm.db.models import (
    SessionLocal, Portfolio, PortfolioNavDaily, 
    PortfolioPositionDaily, Asset, Price,
    AssetClassReturnDaily
)

# 새로운 스키마 import
from schemas_new import (
    # Portfolio responses
    PortfolioListResponse, PortfolioSummaryResponse, PortfoliosResponse,
    NavChartDataPoint, PortfolioWithChartResponse,
    
    # Performance responses
    PerformanceDataPoint, PerformanceResponse, PerformanceAllTimeResponse, PerformanceCustomPeriodResponse,
    RecentReturnData, DailyReturnPoint, BenchmarkReturn,
    
    # Attribution responses
    AssetClassAttributionResponse, AssetAttributionResponse, AttributionResponse,
    
    # Holdings & Assets responses
    AssetHoldingResponse, PortfolioHoldingsResponse, AssetDetailResponse,
    
    # Risk responses
    RiskMetricsResponse, AllocationResponse, RiskAndAllocationResponse,
    
    # Common types
    TimePeriod
)

app = FastAPI(
    title="PortfolioPulse API",
    version="3.0.0",
    description="Mobile-first portfolio management API for external reporting",
    docs_url="/api/docs",              # ← Swagger UI 경로를 /api로
    openapi_url="/api/openapi.json",   # ← 스펙 경로도 /api로
    redoc_url=None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def parse_custom_period(custom_week: Optional[str], custom_month: Optional[str]) -> tuple[date, date, str]:
    """
    커스텀 기간 문자열을 파싱해서 시작일/종료일 반환
    
    Args:
        custom_week: "2024-W01" 형식의 주차 문자열
        custom_month: "2024-01" 형식의 월 문자열
    
    Returns:
        tuple: (start_date, end_date, period_type)
    """
    from datetime import datetime, timedelta
    import re
    
    if custom_week:
        # 주차 파싱: "2024-W01" -> 2024년 1주차 (ISO 8601 표준)
        match = re.match(r"(\d{4})-W(\d{2})", custom_week)
        if match:
            year, week = int(match.group(1)), int(match.group(2))
            
            # Python 표준 라이브러리를 사용한 간단한 방법
            # 해당 연도의 첫 번째 목요일 찾기 (ISO 8601 기준)
            jan4 = datetime(year, 1, 4).date()  # 1월 4일은 항상 첫 번째 주에 포함
            
            # 1월 4일이 포함된 주의 월요일 찾기
            days_since_monday = jan4.weekday()  # 0=Monday, 6=Sunday
            first_week_monday = jan4 - timedelta(days=days_since_monday)
            
            # 지정된 주의 월요일과 일요일 계산
            week_start = first_week_monday + timedelta(weeks=week-1)
            week_end = week_start + timedelta(days=6)
            
            return week_start, week_end, "week"
    
    if custom_month:
        # 월 파싱: "2024-01" -> 2024년 1월
        match = re.match(r"(\d{4})-(\d{2})", custom_month)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            
            # 해당 월의 첫째 날
            month_start = date(year, month, 1)
            
            # 해당 월의 마지막 날
            if month == 12:
                next_month_start = date(year + 1, 1, 1)
            else:
                next_month_start = date(year, month + 1, 1)
            month_end = next_month_start - timedelta(days=1)
            
            return month_start, month_end, "month"
    
    # 기본값: 현재 월
    today = date.today()
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)
    month_end = next_month_start - timedelta(days=1)
    
    return month_start, month_end, "month"

def parse_date_range(period: TimePeriod, portfolio_id: int, db: Session) -> tuple[date, date]:
    """기간 설정에 따른 시작일/종료일 계산"""
    # 최신 데이터 날짜 조회
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == portfolio_id
    ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
    
    if not latest_nav:
        raise HTTPException(status_code=404, detail="No data found for portfolio")
    
    end_date = latest_nav.as_of_date
    
    if period == TimePeriod.ALL or period == TimePeriod.INCEPTION:
        # 투자 시작일부터
        first_nav = db.query(PortfolioNavDaily).filter(
            PortfolioNavDaily.portfolio_id == portfolio_id
        ).order_by(PortfolioNavDaily.as_of_date).first()
        start_date = first_nav.as_of_date if first_nav else end_date
    elif period == TimePeriod.YTD:
        # 올해 시작부터
        start_date = date(end_date.year, 1, 1)
    elif period == TimePeriod.ONE_MONTH:
        start_date = end_date - timedelta(days=30)
    elif period == TimePeriod.THREE_MONTHS:
        start_date = end_date - timedelta(days=90)
    elif period == TimePeriod.SIX_MONTHS:
        start_date = end_date - timedelta(days=180)
    elif period == TimePeriod.ONE_YEAR:
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)  # 기본값: 1개월
    
    return start_date, end_date

def safe_float(value) -> Optional[float]:
    """안전하게 float로 변환"""
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# TODO: 벤치마크 지수 데이터 가져오는 함수 (추후 구현)
def get_benchmark_value(date: date, benchmark_index: str = "SP500") -> Optional[float]:
    """
    특정 날짜의 벤치마크 지수 값을 가져옴
    
    Args:
        date: 조회할 날짜
        benchmark_index: 벤치마크 지수 종류 ("SP500", "KOSPI", "NASDAQ" 등)
    
    Returns:
        해당 날짜의 벤치마크 지수 값 (None if not found)
    
    예시:
        # S&P 500 지수 값 조회
        sp500_value = get_benchmark_value(date(2024, 1, 1), "SP500")
        
        # KOSPI 지수 값 조회  
        kospi_value = get_benchmark_value(date(2024, 1, 1), "KOSPI")
    """
    # TODO: 실제 벤치마크 데이터베이스나 API에서 데이터 조회
    # 예시: 외부 API (Yahoo Finance, Alpha Vantage 등) 또는 내부 DB 테이블
    pass

# ================================
# API ENDPOINTS
# ================================

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "message": "PortfolioPulse API v3.0 is running"}

@app.get("/api/portfolios", response_model=PortfoliosResponse)
async def get_portfolios(
    include_kpi: bool = Query(True, description="KPI 데이터 포함 여부"),
    include_chart: bool = Query(False, description="차트 데이터 포함 여부 (Overview 페이지용)"),
    portfolio_type: Optional[str] = Query(None, description="core 또는 usd_core"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 목록 조회 (Overview 페이지용)
    - include_kpi=false: 기본 목록만 (포트폴리오 선택용)
    - include_kpi=true: KPI 포함된 요약 정보
    - include_chart=true: NAV 차트 데이터 포함 (Overview 페이지용)
    - portfolio_type: core(ID:1) / usd_core(ID:3) 필터링
    """
    try:
        # 포트폴리오 기본 쿼리
        query = db.query(Portfolio)
        
        # 포트폴리오 타입 필터링 (ID 기반)
        if portfolio_type == "core":
            query = query.filter(Portfolio.id == 1)
        elif portfolio_type == "usd_core":
            query = query.filter(Portfolio.id == 3)
        
        portfolios = query.all()
        
        if not include_kpi:
            # 기본 목록만 반환
            portfolio_list = [
                PortfolioListResponse(
                    id=p.id,
                    name=p.name,
                    currency=p.currency
                ) for p in portfolios
            ]
            return PortfoliosResponse(portfolios=portfolio_list)
        
        # KPI 포함된 요약 정보 생성
        portfolio_summaries = []
        
        for portfolio in portfolios:
            # 최신 NAV 데이터 (cash_balance 포함)
            latest_nav = db.query(PortfolioNavDaily).filter(
                PortfolioNavDaily.portfolio_id == portfolio.id
            ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
            
            # 첫 번째 NAV (수익률 계산용)
            first_nav = db.query(PortfolioNavDaily).filter(
                PortfolioNavDaily.portfolio_id == portfolio.id
            ).order_by(PortfolioNavDaily.as_of_date).first()
            
            # TODO: 최신 리스크 메트릭 - 추후 연결 예정
            # latest_risk = db.query(PortfolioRiskMetrics).filter(
            #     PortfolioRiskMetrics.portfolio_id == portfolio.id
            # ).order_by(desc(PortfolioRiskMetrics.date)).first()
            
            # KPI 계산
            nav = safe_float(latest_nav.nav) if latest_nav else None
            total_return = None
            cash_ratio = None
            
            if latest_nav and first_nav and first_nav.nav and first_nav.nav > 0:
                total_return = ((latest_nav.nav - first_nav.nav) / first_nav.nav) * 100
            
            # 현금 비중 계산 (cash_balance / nav * 100)
            if latest_nav and latest_nav.nav and latest_nav.nav > 0 and latest_nav.cash_balance is not None:
                cash_ratio = (safe_float(latest_nav.cash_balance) / safe_float(latest_nav.nav)) * 100
            
            # 차트 데이터가 요청된 경우
            if include_chart:
                # NAV 히스토리 데이터 조회 (최근 1년 또는 전체)
                nav_history = db.query(PortfolioNavDaily).filter(
                    PortfolioNavDaily.portfolio_id == portfolio.id
                ).order_by(PortfolioNavDaily.as_of_date).all()
                
                chart_data = []
                if nav_history:
                    # 첫 번째 NAV를 기준값으로 설정
                    base_nav = nav_history[0].nav
                    
                    for nav_record in nav_history:
                        if nav_record.nav and base_nav and base_nav > 0:
                            # 실제 NAV 값
                            nav_value = float(nav_record.nav)
                            
                            # TODO: 벤치마크 지수 추가 예정
                            # 현재는 임시로 연 5% 복리 성장률 사용
                            # 나중에 실제 벤치마크 지수 (S&P 500, KOSPI 등)로 교체
                            days_diff = (nav_record.as_of_date - nav_history[0].as_of_date).days
                            benchmark_value = float(base_nav) * ((1 + 0.05) ** (days_diff / 365.25))
                            
                            # TODO: 실제 벤치마크 데이터 구조 예시
                            # benchmark_value = get_benchmark_value(nav_record.as_of_date, benchmark_index="SP500")
                            
                            chart_point = {
                                "date": nav_record.as_of_date,
                                "nav": nav_value,
                                "benchmark": benchmark_value  # 나중에 실제 벤치마크 지수로 교체
                            }
                            chart_data.append(chart_point)
                
                portfolio_with_chart = {
                    "id": portfolio.id,
                    "name": portfolio.name,
                    "currency": portfolio.currency,
                    "total_return": total_return,
                    "sharpe_ratio": None,
                    "nav": nav,
                    "cash_ratio": cash_ratio,
                    "chart_data": chart_data
                }
                
                portfolio_summaries.append(portfolio_with_chart)
            else:
                portfolio_summary = PortfolioSummaryResponse(
                    id=portfolio.id,
                    name=portfolio.name,
                    currency=portfolio.currency,
                    total_return=total_return,
                    sharpe_ratio=None,  # TODO: 추후 리스크 메트릭 연결 시 활성화
                    nav=nav,
                    cash_ratio=cash_ratio
                )
                
                portfolio_summaries.append(portfolio_summary)
        
        return PortfoliosResponse(portfolios=portfolio_summaries)
        
    except Exception as e:
        print(f"Error in get_portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}/performance")
async def get_portfolio_performance(
    portfolio_id: int,
    period: str = Query("all", description="분석 기간"),
    custom_week: Optional[str] = Query(None, description="커스텀 주차 (YYYY-WNN 형식)"),
    custom_month: Optional[str] = Query(None, description="커스텀 월 (YYYY-MM 형식)"),
    chart_period: Optional[str] = Query("all", description="차트 기간 (all/1m/1w) - All Time에서만 사용"),
    db: Session = Depends(get_db)
):
    """포트폴리오 성과 데이터 조회 (Performance 페이지용)"""
    try:
        # All time 기간에 대한 특별 처리
        if period == "all":
            return await get_performance_all_time(portfolio_id, chart_period, db)
        
        # Custom 기간에 대한 처리
        elif period == "custom":
            return await get_performance_custom_period(portfolio_id, custom_week, custom_month, db)
        
        # 다른 기간들은 향후 구현
        else:
            return {"message": f"Period '{period}' not yet implemented"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_portfolio_performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_performance_custom_period(
    portfolio_id: int, 
    custom_week: Optional[str], 
    custom_month: Optional[str], 
    db: Session
) -> PerformanceCustomPeriodResponse:
    """Custom Period 성과 데이터 조회"""
    
    # 커스텀 기간 파싱
    start_date, end_date, period_type = parse_custom_period(custom_week, custom_month)
    
    # 디버깅: 파싱된 날짜 범위 로깅
    print(f"🔍 Custom Period Debug:")
    print(f"  - Custom Week: {custom_week}")
    print(f"  - Custom Month: {custom_month}")
    print(f"  - Parsed Start Date: {start_date} ({start_date.strftime('%A')})")
    print(f"  - Parsed End Date: {end_date} ({end_date.strftime('%A')})")
    print(f"  - Period Type: {period_type}")
    
    # 일별 수익률 계산을 위해 시작일 이전 데이터도 포함해서 조회
    # 주간의 경우 최대 3일 전까지, 월간의 경우 최대 5일 전까지 조회
    extended_start_date = start_date - timedelta(days=7 if period_type == "week" else 10)
    
    # 확장된 기간으로 NAV 데이터 조회
    all_nav_data = db.query(PortfolioNavDaily).filter(
        and_(
            PortfolioNavDaily.portfolio_id == portfolio_id,
            PortfolioNavDaily.as_of_date >= extended_start_date,
            PortfolioNavDaily.as_of_date <= end_date
        )
    ).order_by(PortfolioNavDaily.as_of_date).all()
    
    # 실제 기간 내 데이터만 필터링 (누적 수익률 계산용)
    nav_data = [nav for nav in all_nav_data if start_date <= nav.as_of_date <= end_date]
    
    # 디버깅: 조회된 데이터 로깅
    print(f"🔍 Retrieved NAV Data:")
    print(f"  - Extended period: {extended_start_date} to {end_date}")
    print(f"  - Found {len(all_nav_data)} total records")
    print(f"  - Found {len(nav_data)} records in target period")
    for nav in all_nav_data:
        in_period = start_date <= nav.as_of_date <= end_date
        print(f"    {nav.as_of_date} ({nav.as_of_date.strftime('%A')}): NAV = {nav.nav} {'[IN PERIOD]' if in_period else '[EXTENDED]'}")
    
    if not nav_data:
        raise HTTPException(status_code=404, detail=f"No NAV data found for period {start_date} to {end_date}")
    
    # 1. 기간 누적 수익률 계산 (전 영업일 대비)
    cumulative_return = calculate_cumulative_return_with_extended_data(all_nav_data, start_date, end_date)
    
    # 2. 기간 중 일별 수익률 계산 (확장된 데이터 사용하여 전일 대비 계산)
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

def calculate_cumulative_return(nav_data: List) -> float:
    """기간 누적 수익률 계산"""
    if len(nav_data) < 2:
        return 0.0
    
    first_nav = safe_float(nav_data[0].nav)
    last_nav = safe_float(nav_data[-1].nav)
    
    if not first_nav or first_nav <= 0:
        return 0.0
    
    cumulative_return = ((last_nav - first_nav) / first_nav) * 100
    return cumulative_return

def calculate_cumulative_return_with_extended_data(all_nav_data: List, start_date: date, end_date: date) -> float:
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
    
    print(f"🔍 Cumulative Return Calculation:")
    print(f"    Start NAV ({pre_period_data[-1].as_of_date}): {start_nav}")
    print(f"    End NAV ({period_data[-1].as_of_date}): {end_nav}")
    print(f"    Cumulative Return: {cumulative_return:.4f}%")
    
    return cumulative_return

def calculate_period_daily_returns_with_extended_data(all_nav_data: List, start_date: date, end_date: date) -> List[DailyReturnPoint]:
    """확장된 데이터를 사용해서 기간 중 일별 수익률 계산 (전일 대비)"""
    if len(all_nav_data) < 2:
        print(f"🔍 Daily Returns: Not enough data ({len(all_nav_data)} records)")
        return []
    
    daily_returns = []
    
    print(f"🔍 Daily Returns Calculation (with extended data):")
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
                daily_return=daily_return
            ))
            print(f"    {curr_nav_record.as_of_date} ({curr_nav_record.as_of_date.strftime('%A')}): {daily_return:.4f}% (from {prev_nav_record.as_of_date}: {prev_nav} to {curr_nav})")
        else:
            print(f"    {curr_nav_record.as_of_date} ({curr_nav_record.as_of_date.strftime('%A')}): SKIPPED (prev_nav={prev_nav}, curr_nav={curr_nav})")
    
    print(f"🔍 Total daily returns generated: {len(daily_returns)}")
    return daily_returns

def calculate_period_daily_returns(nav_data: List) -> List[DailyReturnPoint]:
    """기간 중 일별 수익률 계산"""
    if len(nav_data) < 2:
        print(f"🔍 Daily Returns: Not enough data ({len(nav_data)} records)")
        return []
    
    daily_returns = []
    
    print(f"🔍 Daily Returns Calculation:")
    for i in range(1, len(nav_data)):
        prev_nav = safe_float(nav_data[i-1].nav)
        curr_nav = safe_float(nav_data[i].nav)
        
        if prev_nav and prev_nav > 0 and curr_nav:
            daily_return = ((curr_nav - prev_nav) / prev_nav) * 100
            daily_returns.append(DailyReturnPoint(
                date=nav_data[i].as_of_date,
                daily_return=daily_return
            ))
            print(f"    {nav_data[i].as_of_date} ({nav_data[i].as_of_date.strftime('%A')}): {daily_return:.4f}% (from {prev_nav} to {curr_nav})")
        else:
            print(f"    {nav_data[i].as_of_date} ({nav_data[i].as_of_date.strftime('%A')}): SKIPPED (prev_nav={prev_nav}, curr_nav={curr_nav})")
    
    print(f"🔍 Total daily returns generated: {len(daily_returns)}")
    return daily_returns

async def calculate_benchmark_returns_custom_period(
    portfolio_id: int, 
    start_date: date, 
    end_date: date, 
    portfolio_return: float,
    db: Session
) -> List[BenchmarkReturn]:
    """Custom Period 벤치마크 대비 수익률 계산"""
    
    # 현재는 실제 벤치마크 데이터가 없으므로 빈 리스트 반환
    # TODO: 실제 벤치마크 지수 데이터 연동 후 활성화
    return []
    
    # 실제 구현 예시 (주석 처리)
    # benchmarks = [
    #     {
    #         "name": "KOSPI",
    #         "return": get_benchmark_period_return("KOSPI", start_date, end_date),
    #     },
    #     {
    #         "name": "KOSPI 200", 
    #         "return": get_benchmark_period_return("KOSPI200", start_date, end_date),
    #     },
    #     {
    #         "name": "S&P 500",
    #         "return": get_benchmark_period_return("SPX", start_date, end_date),
    #     }
    # ]
    
    # benchmark_returns = []
    # for benchmark in benchmarks:
    #     if benchmark["return"] is not None:
    #         outperformance = portfolio_return - benchmark["return"]
    #         benchmark_returns.append(BenchmarkReturn(
    #             name=benchmark["name"],
    #             return_pct=benchmark["return"],
    #             outperformance=outperformance
    #         ))
    
    # return benchmark_returns

async def get_performance_all_time(portfolio_id: int, chart_period: str, db: Session) -> PerformanceAllTimeResponse:
    """All Time 성과 데이터 조회"""
    
    # 최신 NAV 데이터 조회
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == portfolio_id
    ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
    
    if not latest_nav:
        raise HTTPException(status_code=404, detail="No NAV data found")
    
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
        raise HTTPException(status_code=404, detail="No recent NAV data found")
    
    # 1. Recent Returns 계산 (1일/1주/1개월)
    recent_returns = calculate_recent_returns(recent_nav_data)
    
    # 2. 차트용 일별 수익률 데이터 (chart_period에 따라 기간 조정)
    chart_daily_returns = calculate_chart_daily_returns(portfolio_id, chart_period, end_date, db)
    
    # 3. 벤치마크 대비 수익률 (All Time)
    benchmark_returns = await calculate_benchmark_returns_all_time(portfolio_id, db)
    
    return PerformanceAllTimeResponse(
        recent_returns=recent_returns,
        recent_week_daily_returns=chart_daily_returns,  # 이제 chart_period에 따라 다른 데이터
        daily_returns=chart_daily_returns,  # 차트용 일별 수익률 데이터
        benchmark_returns=benchmark_returns
    )

def calculate_recent_returns(nav_data: List) -> RecentReturnData:
    """최근 수익률 계산"""
    if len(nav_data) < 2:
        return RecentReturnData()
    
    # 최신 NAV
    latest_nav = safe_float(nav_data[-1].nav)
    
    # 1일 수익률
    daily_return = None
    if len(nav_data) >= 2:
        prev_nav = safe_float(nav_data[-2].nav)
        if prev_nav and prev_nav > 0 and latest_nav:
            daily_return = ((latest_nav - prev_nav) / prev_nav) * 100
    
    # 1주 수익률 (7일 전과 비교)
    weekly_return = None
    if len(nav_data) >= 8:
        week_ago_nav = safe_float(nav_data[-8].nav)
        if week_ago_nav and week_ago_nav > 0 and latest_nav:
            weekly_return = ((latest_nav - week_ago_nav) / week_ago_nav) * 100
    
    # 1개월 수익률 (30일 전과 비교, 또는 가장 오래된 데이터와 비교)
    monthly_return = None
    if len(nav_data) >= 1:
        oldest_nav = safe_float(nav_data[0].nav)
        if oldest_nav and oldest_nav > 0 and latest_nav:
            monthly_return = ((latest_nav - oldest_nav) / oldest_nav) * 100
    
    return RecentReturnData(
        daily_return=daily_return,
        weekly_return=weekly_return,
        monthly_return=monthly_return
    )

def calculate_recent_week_daily_returns(nav_data: List) -> List[DailyReturnPoint]:
    """최근 주간 일별 수익률 계산"""
    if len(nav_data) < 2:
        return []
    
    # 최근 7일 또는 사용 가능한 데이터
    recent_data = nav_data[-7:] if len(nav_data) >= 7 else nav_data
    daily_returns = []
    
    for i in range(1, len(recent_data)):
        prev_nav = safe_float(recent_data[i-1].nav)
        curr_nav = safe_float(recent_data[i].nav)
        
        if prev_nav and prev_nav > 0 and curr_nav:
            daily_return = ((curr_nav - prev_nav) / prev_nav) * 100
            daily_returns.append(DailyReturnPoint(
                date=recent_data[i].as_of_date,
                daily_return=daily_return
            ))
    
    return daily_returns

def calculate_chart_daily_returns(portfolio_id: int, chart_period: str, end_date: date, db: Session) -> List[DailyReturnPoint]:
    """차트용 일별 수익률 계산 (기간별)"""
    
    # chart_period에 따라 시작일 결정
    if chart_period == "1w":
        start_date = end_date - timedelta(days=7)
        days_needed = 8  # 수익률 계산을 위해 하루 더 필요
    elif chart_period == "1m":
        start_date = end_date - timedelta(days=30)
        days_needed = 31  # 수익률 계산을 위해 하루 더 필요
    else:  # "all"
        # 전체 기간: 포트폴리오 시작부터 (최대 1년으로 제한)
        start_date = end_date - timedelta(days=365)
        days_needed = 366
    
    # 수익률 계산을 위해 시작일보다 하루 더 일찍부터 조회
    extended_start_date = start_date - timedelta(days=1)
    
    print(f"🔍 Chart Daily Returns ({chart_period}):")
    print(f"  - End Date: {end_date}")
    print(f"  - Start Date: {start_date}")
    print(f"  - Extended Start Date: {extended_start_date}")
    
    # NAV 데이터 조회
    nav_data = db.query(PortfolioNavDaily).filter(
        and_(
            PortfolioNavDaily.portfolio_id == portfolio_id,
            PortfolioNavDaily.as_of_date >= extended_start_date,
            PortfolioNavDaily.as_of_date <= end_date
        )
    ).order_by(PortfolioNavDaily.as_of_date).all()
    
    print(f"  - Found {len(nav_data)} NAV records")
    
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
                daily_return=daily_return
            ))
            print(f"    {curr_nav_record.as_of_date}: {daily_return:.4f}%")
    
    print(f"  - Generated {len(daily_returns)} daily returns")
    return daily_returns

async def calculate_benchmark_returns_all_time(portfolio_id: int, db: Session) -> List[BenchmarkReturn]:
    """All Time 벤치마크 대비 수익률 계산"""
    
    # 현재는 실제 벤치마크 데이터가 없으므로 빈 리스트 반환
    # TODO: 실제 벤치마크 지수 데이터 (KOSPI, KOSPI200, S&P500) 연동 후 활성화
    return []
    
    # 포트폴리오 전체 기간 수익률 계산
    first_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == portfolio_id
    ).order_by(PortfolioNavDaily.as_of_date).first()
    
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == portfolio_id
    ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
    
    if not first_nav or not latest_nav:
        return []
    
    # 포트폴리오 총 수익률
    first_nav_value = safe_float(first_nav.nav)
    latest_nav_value = safe_float(latest_nav.nav)
    
    if not first_nav_value or not latest_nav_value or first_nav_value <= 0:
        return []
    
    portfolio_total_return = ((latest_nav_value - first_nav_value) / first_nav_value) * 100
    
    # 실제 벤치마크 데이터 연동 예시 코드 (미구현)
    # benchmarks = [
    #     {
    #         "name": "KOSPI",
    #         "return": get_benchmark_return("KOSPI", first_nav.as_of_date, latest_nav.as_of_date),
    #     },
    #     {
    #         "name": "KOSPI 200", 
    #         "return": get_benchmark_return("KOSPI200", first_nav.as_of_date, latest_nav.as_of_date),
    #     },
    #     {
    #         "name": "S&P 500",
    #         "return": get_benchmark_return("SPX", first_nav.as_of_date, latest_nav.as_of_date),
    #     }
    # ]
    
    # benchmark_returns = []
    # for benchmark in benchmarks:
    #     if benchmark["return"] is not None:
    #         outperformance = portfolio_total_return - benchmark["return"]
    #         benchmark_returns.append(BenchmarkReturn(
    #             name=benchmark["name"],
    #             return_pct=benchmark["return"],
    #             outperformance=outperformance
    #         ))
    
    # return benchmark_returns

@app.get("/api/portfolios/{portfolio_id}/attribution", response_model=AttributionResponse)
async def get_portfolio_attribution(
    portfolio_id: int,
    period: TimePeriod = Query(TimePeriod.INCEPTION, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """포트폴리오 기여도 분석 데이터 조회 (Attribution 페이지용) - 현재 미구현"""
    try:
        # TODO: Attribution 테이블들이 구현되면 활성화
        return AttributionResponse(
            asset_class_attributions=[],
            top_contributors=[],
            period=period,
            start_date=date.today(),
            end_date=date.today()
        )
        
    except Exception as e:
        print(f"Error in get_portfolio_attribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}/holdings", response_model=PortfolioHoldingsResponse)
async def get_portfolio_holdings(
    portfolio_id: int,
    as_of_date: Optional[date] = Query(None, description="기준일 (기본값: 최신일)"),
    db: Session = Depends(get_db)
):
    """포트폴리오 보유 자산 현황 조회 (Assets 페이지용)"""
    try:
        # 기준일 설정
        if not as_of_date:
            latest_position = db.query(PortfolioPositionDaily).filter(
                PortfolioPositionDaily.portfolio_id == portfolio_id
            ).order_by(desc(PortfolioPositionDaily.as_of_date)).first()
            
            if not latest_position:
                raise HTTPException(status_code=404, detail="No holdings data found")
            
            as_of_date = latest_position.as_of_date
        
        # 포지션 데이터 조회
        positions = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.as_of_date == as_of_date,
                PortfolioPositionDaily.quantity > 0  # 보유 중인 자산만
            )
        ).all()
        
        holdings = []
        total_market_value = 0.0
        
        for position in positions:
            asset = db.query(Asset).filter(Asset.id == position.asset_id).first()
            if not asset:
                continue
            
            # 현재가 조회
            latest_price = db.query(Price).filter(
                and_(
                    Price.asset_id == position.asset_id,
                    Price.date <= as_of_date
                )
            ).order_by(desc(Price.date)).first()
            
            current_price = safe_float(latest_price.close) if latest_price else 0.0
            quantity = safe_float(position.quantity) or 0.0
            avg_price = safe_float(position.avg_cost) or current_price
            
            market_value = quantity * current_price
            unrealized_pnl = (current_price - avg_price) * quantity
            
            # 일일 변동률 계산 (전일 대비)
            day_change = 0.0
            if latest_price and latest_price.previous_close:
                day_change = ((current_price - latest_price.previous_close) / latest_price.previous_close) * 100
            
            holding = AssetHoldingResponse(
                id=asset.id,
                name=asset.name or asset.ticker,
                ticker=asset.ticker,
                quantity=quantity,
                avg_price=avg_price,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                day_change=day_change,
                weight=0.0  # 나중에 계산
            )
            
            holdings.append(holding)
            total_market_value += market_value
        
        # 비중 계산
        for holding in holdings:
            if total_market_value > 0:
                holding.weight = (holding.market_value / total_market_value) * 100
        
        # 현금 잔고 조회 (NAV - 총 시장가치)
        latest_nav = db.query(PortfolioNavDaily).filter(
            and_(
                PortfolioNavDaily.portfolio_id == portfolio_id,
                PortfolioNavDaily.as_of_date == as_of_date
            )
        ).first()
        
        nav_value = safe_float(latest_nav.nav) if latest_nav else total_market_value
        cash_balance = nav_value - total_market_value
        
        return PortfolioHoldingsResponse(
            holdings=holdings,
            total_market_value=total_market_value,
            cash_balance=max(0.0, cash_balance),  # 음수 방지
            total_value=nav_value,
            as_of_date=as_of_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_portfolio_holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}/assets/{asset_id}", response_model=AssetDetailResponse)
async def get_asset_detail(
    portfolio_id: int,
    asset_id: int,
    period: TimePeriod = Query(TimePeriod.INCEPTION, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """개별 자산 상세 정보 조회 (Assets 페이지 디테일 시트용)"""
    try:
        # 자산 기본 정보
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        start_date, end_date = parse_date_range(period, portfolio_id, db)
        
        # 현재 포지션
        latest_position = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.asset_id == asset_id
            )
        ).order_by(desc(PortfolioPositionDaily.as_of_date)).first()
        
        # 가격 히스토리
        price_history = db.query(Price).filter(
            and_(
                Price.asset_id == asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            )
        ).order_by(Price.date).all()
        
        # 누적 수익률 계산
        cumulative_return = 0.0
        if price_history and len(price_history) > 1:
            first_price = price_history[0].close
            latest_price = price_history[-1].close
            if first_price and first_price > 0:
                cumulative_return = ((latest_price - first_price) / first_price) * 100
        
        # 포지션 정보
        quantity = safe_float(latest_position.quantity) if latest_position else 0.0
        avg_cost = safe_float(latest_position.avg_cost) if latest_position else 0.0
        current_price = safe_float(price_history[-1].close) if price_history else 0.0
        
        unrealized_pnl = (current_price - avg_cost) * quantity if quantity > 0 else 0.0
        
        return AssetDetailResponse(
            id=asset.id,
            name=asset.name or asset.ticker,
            ticker=asset.ticker,
            currency=asset.currency,
            asset_class=asset.asset_class,
            quantity=quantity,
            avg_cost=avg_cost,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            cumulative_return=cumulative_return,
            price_history=[
                {
                    "date": p.date,
                    "price": safe_float(p.close)
                } for p in price_history
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_asset_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolios/{portfolio_id}/risk-allocation", response_model=RiskAndAllocationResponse)
async def get_risk_and_allocation(
    portfolio_id: int,
    period: TimePeriod = Query(TimePeriod.INCEPTION, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """포트폴리오 리스크 및 배분 현황 조회 (Risk & Allocation 페이지용) - 현재 미구현"""
    try:
        # TODO: Risk 및 Allocation 테이블들이 구현되면 활성화
        return RiskAndAllocationResponse(
            risk_metrics=None,
            sector_allocation=[],
            period=period,
            start_date=date.today(),
            end_date=date.today()
        )
        
    except Exception as e:
        print(f"Error in get_risk_and_allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

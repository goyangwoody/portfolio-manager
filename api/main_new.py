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
    PerformanceDataPoint, PerformanceResponse,
    
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
    description="Mobile-first portfolio management API for external reporting"
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
def parse_date_range(period: TimePeriod, portfolio_id: int, db: Session) -> tuple[date, date]:
    """기간 설정에 따른 시작일/종료일 계산"""
    # 최신 데이터 날짜 조회
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == portfolio_id
    ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
    
    if not latest_nav:
        raise HTTPException(status_code=404, detail="No data found for portfolio")
    
    end_date = latest_nav.as_of_date
    
    if period == TimePeriod.INCEPTION:
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

@app.get("/api/portfolios/{portfolio_id}/performance", response_model=PerformanceResponse)
async def get_portfolio_performance(
    portfolio_id: int,
    period: TimePeriod = Query(TimePeriod.INCEPTION, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """포트폴리오 성과 데이터 조회 (Performance 페이지용)"""
    try:
        start_date, end_date = parse_date_range(period, portfolio_id, db)
        
        # NAV 데이터 조회
        nav_data = db.query(PortfolioNavDaily).filter(
            and_(
                PortfolioNavDaily.portfolio_id == portfolio_id,
                PortfolioNavDaily.as_of_date >= start_date,
                PortfolioNavDaily.as_of_date <= end_date
            )
        ).order_by(PortfolioNavDaily.as_of_date).all()
        
        if not nav_data:
            raise HTTPException(status_code=404, detail="No performance data found")
        
        # 성과 데이터 포인트 생성
        performance_points = []
        benchmark_base = 100.0  # 벤치마크 기준값 (임시)
        
        for nav in nav_data:
            # 일일 수익률 계산 (전일 대비)
            daily_return = None
            if nav.daily_return:
                daily_return = safe_float(nav.daily_return) * 100  # 퍼센트로 변환
            
            performance_point = PerformanceDataPoint(
                date=nav.as_of_date,
                portfolio_value=safe_float(nav.nav),
                benchmark_value=benchmark_base,  # 임시 벤치마크 값
                daily_return=daily_return
            )
            performance_points.append(performance_point)
        
        return PerformanceResponse(
            data=performance_points,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_portfolio_performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

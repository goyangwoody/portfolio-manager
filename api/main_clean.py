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
    AttributionAllTimeResponse, AttributionSpecificPeriodResponse, AttributionCustomPeriodResponse,
    AssetContribution, AssetClassContribution, DailyPortfolioReturn, AssetWeightTrend, AssetReturnTrend,
    AssetDetailResponse, PricePerformancePoint, AssetFilter,
    
    # Holdings & Assets responses
    AssetHoldingResponse, PortfolioHoldingsResponse,
    
    # Risk responses
    RiskMetricsResponse, AllocationResponse, RiskAndAllocationResponse,
    
    # Common types
    TimePeriod
)

app = FastAPI(
    title="PortfolioPulse API",
    version="3.0.0",
    description="Mobile-first portfolio management API for external reporting",
    root_path="/api",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# DATABASE CONNECTION
# ================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================================
# HELPER FUNCTIONS
# ================================

def parse_custom_period(custom_week: Optional[str], custom_month: Optional[str]) -> tuple[date, date, str]:
    """
    커스텀 기간 파싱
    
    Args:
        custom_week: "2024-W23" 형식의 주간 선택
        custom_month: "2024-03" 형식의 월간 선택
    
    Returns:
        (start_date, end_date, period_type)
    """
    if custom_week:
        # 주간 기간 파싱 "2024-W23" -> 해당 주의 월~일
        year_str, week_str = custom_week.split('-W')
        year = int(year_str)
        week = int(week_str)
        
        # 해당 년도의 첫 번째 월요일 찾기
        jan_1 = date(year, 1, 1)
        first_monday = jan_1 + timedelta(days=(7 - jan_1.weekday()) % 7)
        
        # 해당 주의 월요일 계산
        week_start = first_monday + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)
        
        return week_start, week_end, "week"
    
    elif custom_month:
        # 월간 기간 파싱 "2024-03" -> 해당 월의 1일~말일
        year_str, month_str = custom_month.split('-')
        year = int(year_str)
        month = int(month_str)
        
        month_start = date(year, month, 1)
        
        # 다음 달 1일에서 하루 빼기 = 해당 월 마지막 날
        if month == 12:
            next_month_start = date(year + 1, 1, 1)
        else:
            next_month_start = date(year, month + 1, 1)
        
        month_end = next_month_start - timedelta(days=1)
        
        return month_start, month_end, "month"
    
    else:
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
    """기간 타입에 따른 시작/끝 날짜 계산"""
    end_date = date.today()
    
    if period in [TimePeriod.ALL, TimePeriod.INCEPTION]:
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

def get_benchmark_value(date: date, benchmark_index: str = "SP500") -> Optional[float]:
    """
    특정 날짜의 벤치마크 지수 값을 가져옴 (추후 구현)
    """
    # TODO: 실제 벤치마크 데이터베이스나 API에서 데이터 조회
    pass

# ================================
# TWR ATTRIBUTION CALCULATION
# ================================

def calculate_detailed_twr_attribution(
    db: Session, 
    portfolio_id: int, 
    start_date: date, 
    end_date: date,
    asset_filter: AssetFilter = AssetFilter.ALL
) -> dict:
    """
    상세한 TWR 기반 포트폴리오 기여도 분석 (차트 데이터 포함)
    
    Features:
    - domestic/foreign 필터링
    - 자산클래스별 차트 데이터 (비중 추이, TWR 추이)
    - 개별 자산 상세 데이터
    """
    try:
        # 1. 기간 내 모든 포지션 데이터 조회
        positions_query = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.as_of_date >= start_date,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        )
        
        # 자산 필터 적용
        if asset_filter != AssetFilter.ALL:
            # Asset 테이블과 조인하여 필터링
            positions_query = positions_query.join(Asset).filter(
                Asset.region == asset_filter.value if asset_filter.value in ["domestic", "foreign"] else True
            )
        
        positions = positions_query.order_by(PortfolioPositionDaily.as_of_date).all()
        
        if not positions:
            raise ValueError("No position data found for the specified period and filter")
        
        # 2. 기본 TWR 계산 준비
        positions_by_date = {}
        all_asset_ids = set()
        
        for pos in positions:
            date_key = pos.as_of_date
            if date_key not in positions_by_date:
                positions_by_date[date_key] = {}
            
            positions_by_date[date_key][pos.asset_id] = {
                'quantity': float(pos.quantity or 0),
                'mv_eod': float(pos.mv_eod or 0),
                'asset_id': pos.asset_id
            }
            all_asset_ids.add(pos.asset_id)
        
        # 3. 자산 정보 조회
        assets = db.query(Asset).filter(Asset.id.in_(all_asset_ids)).all()
        asset_info = {asset.id: asset for asset in assets}
        
        # 4. 가격 데이터 조회
        prices = db.query(Price).filter(
            and_(
                Price.asset_id.in_(all_asset_ids),
                Price.date >= start_date,
                Price.date <= end_date
            )
        ).order_by(Price.date).all()
        
        # 가격 데이터를 (asset_id, date) 키로 정리
        price_data = {}
        for price in prices:
            price_data[(price.asset_id, price.date)] = float(price.close)
        
        # 5. 일별 TWR 계산 (간단한 버전)
        sorted_dates = sorted(positions_by_date.keys())
        daily_returns = []
        asset_contributions = {asset_id: 0.0 for asset_id in all_asset_ids}
        
        for i, current_date in enumerate(sorted_dates):
            current_total_mv = sum(pos['mv_eod'] for pos in positions_by_date[current_date].values())
            
            daily_returns.append(DailyPortfolioReturn(
                date=current_date,
                daily_return=0.0,  # 실제 계산이 필요
                portfolio_value=current_total_mv
            ))
        
        # 6. 총 TWR 계산 (간단한 버전)
        if sorted_dates:
            first_mv = sum(pos['mv_eod'] for pos in positions_by_date[sorted_dates[0]].values())
            last_mv = sum(pos['mv_eod'] for pos in positions_by_date[sorted_dates[-1]].values())
            total_twr = ((last_mv / first_mv) - 1) * 100 if first_mv > 0 else 0.0
        else:
            total_twr = 0.0
        
        # 7. 자산별 상세 데이터 생성
        asset_details = []
        for asset_id in all_asset_ids:
            if asset_id not in asset_info:
                continue
                
            asset = asset_info[asset_id]
            
            # 현재 배분 (마지막 날 기준)
            last_date = sorted_dates[-1] if sorted_dates else None
            current_allocation = 0.0
            if last_date:
                last_positions = positions_by_date[last_date]
                total_mv = sum(pos['mv_eod'] for pos in last_positions.values())
                asset_mv = last_positions.get(asset_id, {}).get('mv_eod', 0.0)
                current_allocation = (asset_mv / total_mv * 100) if total_mv > 0 else 0.0
            
            asset_detail = AssetContribution(
                asset_id=asset_id,
                ticker=asset.ticker or "",
                name=asset.name or asset.ticker or f"Asset_{asset_id}",
                asset_class=asset.asset_class or "Unknown",
                region=getattr(asset, "region", "unknown"),
                current_allocation=current_allocation,
                current_price=0.0,  # 실제 가격 조회 필요
                avg_weight=current_allocation,  # 임시값
                period_return=0.0,  # 실제 계산 필요
                contribution=asset_contributions[asset_id] * 100
            )
            asset_details.append(asset_detail)
        
        # 8. 자산클래스별 기여도 집계
        asset_class_contributions = {}
        for asset in asset_details:
            ac = asset.asset_class
            if ac not in asset_class_contributions:
                asset_class_contributions[ac] = {
                    'contribution': 0.0,
                    'current_allocation': 0.0,
                    'assets': []
                }
            
            asset_class_contributions[ac]['contribution'] += asset.contribution
            asset_class_contributions[ac]['current_allocation'] += asset.current_allocation
            asset_class_contributions[ac]['assets'].append(asset)
        
        # AssetClassContribution 객체로 변환
        asset_class_list = []
        for ac_name, ac_data in asset_class_contributions.items():
            # 빈 차트 데이터 (실제로는 계산되어야 함)
            weight_trend = [AssetWeightTrend(date=d, weight=ac_data['current_allocation']) for d in sorted_dates[-5:]]
            return_trend = [AssetReturnTrend(date=d, cumulative_twr=0.0, daily_twr=0.0) for d in sorted_dates[-5:]]
            
            asset_class_list.append(AssetClassContribution(
                asset_class=ac_name,
                current_allocation=ac_data['current_allocation'],
                avg_weight=ac_data['current_allocation'],
                contribution=ac_data['contribution'],
                weight_trend=weight_trend,
                return_trend=return_trend,
                assets=ac_data['assets']
            ))
        
        # 9. 상위/하위 기여자 분류
        sorted_assets = sorted(asset_details, key=lambda x: x.contribution, reverse=True)
        top_contributors = [asset for asset in sorted_assets if asset.contribution > 0]
        top_detractors = [asset for asset in sorted_assets if asset.contribution < 0]
        
        return {
            "total_twr": total_twr,
            "daily_returns": daily_returns,
            "asset_class_contributions": asset_class_list,
            "top_contributors": top_contributors,
            "top_detractors": top_detractors,
            "total_contribution_check": sum(asset.contribution for asset in asset_details)
        }
        
    except Exception as e:
        print(f"Error in calculate_detailed_twr_attribution: {e}")
        raise e

def calculate_asset_detail(
    db: Session,
    portfolio_id: int,
    asset_id: int,
    start_date: date,
    end_date: date
) -> AssetDetailResponse:
    """개별 자산 상세 정보 계산"""
    try:
        # 자산 정보 조회
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # 포지션 데이터 조회
        positions = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.asset_id == asset_id,
                PortfolioPositionDaily.as_of_date >= start_date,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).order_by(PortfolioPositionDaily.as_of_date).all()
        
        if not positions:
            raise ValueError(f"No position data found for asset {asset_id}")
        
        # 가격 데이터 조회
        prices = db.query(Price).filter(
            and_(
                Price.asset_id == asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            )
        ).order_by(Price.date).all()
        
        # 현재 정보 계산
        latest_position = positions[-1]
        latest_price = prices[-1] if prices else None
        
        # 포트폴리오 총 가치 계산
        portfolio_total_mv = db.query(func.sum(PortfolioPositionDaily.mv_eod)).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.as_of_date == latest_position.as_of_date
            )
        ).scalar() or 0
        
        current_allocation = (float(latest_position.mv_eod or 0) / portfolio_total_mv * 100) if portfolio_total_mv > 0 else 0.0
        current_price = float(latest_price.close) if latest_price else 0.0
        
        # NAV 수익률 계산
        first_price = prices[0] if prices else None
        nav_return = ((current_price / float(first_price.close)) - 1) * 100 if (first_price and first_price.close) else 0.0
        
        # 가격 성과 차트 데이터
        price_performance = []
        if prices:
            base_price = float(prices[0].close) if prices[0].close else 1.0
            for price in prices:
                normalized_value = (float(price.close) / base_price * 100) if base_price > 0 else 100
                price_performance.append(PricePerformancePoint(
                    date=price.date,
                    price=float(price.close),
                    normalized_value=normalized_value
                ))
        
        return AssetDetailResponse(
            asset_id=asset_id,
            ticker=asset.ticker or "",
            name=asset.name or asset.ticker or f"Asset_{asset_id}",
            asset_class=asset.asset_class or "Unknown",
            region=getattr(asset, "region", "unknown"),
            current_allocation=current_allocation,
            current_price=current_price,
            nav_return=nav_return,
            twr_contribution=0.0,  # 실제 계산 필요
            price_performance=price_performance
        )
        
    except Exception as e:
        print(f"Error in calculate_asset_detail: {e}")
        raise e

# ================================
# API ENDPOINTS
# ================================

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "message": "PortfolioPulse API v3.0 is running"}

@app.get("/portfolios", response_model=PortfoliosResponse)
async def get_portfolios(
    include_kpi: bool = Query(True, description="KPI 데이터 포함 여부"),
    include_chart: bool = Query(False, description="차트 데이터 포함 여부 (Overview 페이지용)"),
    portfolio_type: Optional[str] = Query(None, description="core 또는 usd_core"),
    db: Session = Depends(get_db)
):
    """포트폴리오 목록 조회"""
    try:
        # 포트폴리오 기본 쿼리
        query = db.query(Portfolio)
        
        # 포트폴리오 타입 필터링
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
        
        # KPI 포함된 응답 생성 (간단한 버전)
        portfolio_summaries = []
        for p in portfolios:
            # 최신 NAV 조회
            latest_nav = db.query(PortfolioNavDaily).filter(
                PortfolioNavDaily.portfolio_id == p.id
            ).order_by(desc(PortfolioNavDaily.as_of_date)).first()
            
            portfolio_summary = PortfolioSummaryResponse(
                id=p.id,
                name=p.name,
                currency=p.currency,
                total_return=10.5,  # 실제 계산 필요
                sharpe_ratio=1.2,   # 실제 계산 필요
                nav=float(latest_nav.nav) if latest_nav else 0.0,
                cash_ratio=5.0      # 실제 계산 필요
            )
            
            portfolio_summaries.append(portfolio_summary)
        
        return PortfoliosResponse(portfolios=portfolio_summaries)
        
    except Exception as e:
        print(f"Error in get_portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ATTRIBUTION ENDPOINTS
# ================================

@app.get("/portfolios/{portfolio_id}/attribution/all-time", response_model=AttributionAllTimeResponse)
async def get_portfolio_attribution_all_time(
    portfolio_id: int,
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터 (all/domestic/foreign)"),
    db: Session = Depends(get_db)
):
    """포트폴리오 All Time 기여도 분석 (TWR 기반)"""
    try:
        # 포트폴리오 존재 여부 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # 전체 기간 설정
        first_position = db.query(PortfolioPositionDaily).filter(
            PortfolioPositionDaily.portfolio_id == portfolio_id
        ).order_by(PortfolioPositionDaily.as_of_date).first()
        
        latest_position = db.query(PortfolioPositionDaily).filter(
            PortfolioPositionDaily.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioPositionDaily.as_of_date)).first()
        
        if not first_position or not latest_position:
            raise HTTPException(status_code=404, detail="No position data found")
        
        start_date = first_position.as_of_date
        end_date = latest_position.as_of_date
        
        # TWR 기반 기여도 계산
        attribution_result = calculate_detailed_twr_attribution(
            db, portfolio_id, start_date, end_date, asset_filter
        )
        
        return AttributionAllTimeResponse(
            total_twr=attribution_result["total_twr"],
            daily_returns=attribution_result["daily_returns"],
            asset_class_contributions=attribution_result["asset_class_contributions"],
            top_contributors=attribution_result["top_contributors"],
            top_detractors=attribution_result["top_detractors"],
            asset_filter=asset_filter,
            period=TimePeriod.ALL,
            start_date=start_date,
            end_date=end_date,
            total_contribution_check=attribution_result.get("total_contribution_check")
        )
        
    except Exception as e:
        print(f"Error in get_portfolio_attribution_all_time: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolios/{portfolio_id}/attribution/specific-period", response_model=AttributionSpecificPeriodResponse)
async def get_portfolio_attribution_specific_period(
    portfolio_id: int,
    start_date: date = Query(description="분석 시작일"),
    end_date: date = Query(description="분석 종료일"),
    asset_filter: AssetFilter = Query(AssetFilter.ALL, description="자산 필터 (all/domestic/foreign)"),
    period_type: str = Query("custom", description="기간 타입 (week/month/custom)"),
    db: Session = Depends(get_db)
):
    """포트폴리오 Specific Period 기여도 분석 (TWR 기반)"""
    try:
        # 포트폴리오 존재 여부 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # 날짜 유효성 검사
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        # TWR 기반 기여도 계산
        attribution_result = calculate_detailed_twr_attribution(
            db, portfolio_id, start_date, end_date, asset_filter
        )
        
        return AttributionSpecificPeriodResponse(
            period_twr=attribution_result["total_twr"],
            daily_returns=attribution_result["daily_returns"],
            asset_class_contributions=attribution_result["asset_class_contributions"],
            top_contributors=attribution_result["top_contributors"],
            top_detractors=attribution_result["top_detractors"],
            asset_filter=asset_filter,
            start_date=start_date,
            end_date=end_date,
            period_type=period_type,
            total_contribution_check=attribution_result.get("total_contribution_check")
        )
        
    except Exception as e:
        print(f"Error in get_portfolio_attribution_specific_period: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolios/{portfolio_id}/attribution/asset-detail/{asset_id}", response_model=AssetDetailResponse)
async def get_attribution_asset_detail(
    portfolio_id: int,
    asset_id: int,
    start_date: Optional[date] = Query(None, description="분석 시작일 (기본값: All Time)"),
    end_date: Optional[date] = Query(None, description="분석 종료일 (기본값: 최신일)"),
    db: Session = Depends(get_db)
):
    """개별 자산 상세 정보 조회 (드릴다운용)"""
    try:
        # 포트폴리오와 자산 존재 여부 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # 기간 설정
        if not start_date or not end_date:
            first_position = db.query(PortfolioPositionDaily).filter(
                and_(
                    PortfolioPositionDaily.portfolio_id == portfolio_id,
                    PortfolioPositionDaily.asset_id == asset_id
                )
            ).order_by(PortfolioPositionDaily.as_of_date).first()
            
            latest_position = db.query(PortfolioPositionDaily).filter(
                and_(
                    PortfolioPositionDaily.portfolio_id == portfolio_id,
                    PortfolioPositionDaily.asset_id == asset_id
                )
            ).order_by(desc(PortfolioPositionDaily.as_of_date)).first()
            
            if not first_position or not latest_position:
                raise HTTPException(status_code=404, detail="No position data found for this asset")
            
            start_date = start_date or first_position.as_of_date
            end_date = end_date or latest_position.as_of_date
        
        # 자산 상세 정보 계산
        asset_detail = calculate_asset_detail(
            db, portfolio_id, asset_id, start_date, end_date
        )
        
        return asset_detail
        
    except Exception as e:
        print(f"Error in get_attribution_asset_detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# 레거시 호환성 엔드포인트
# ================================

@app.get("/portfolios/{portfolio_id}/attribution", response_model=AttributionResponse)
async def get_portfolio_attribution_legacy(
    portfolio_id: int,
    period: TimePeriod = Query(TimePeriod.INCEPTION, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """포트폴리오 기여도 분석 (레거시 호환성)"""
    try:
        # All Time 데이터를 레거시 형식으로 변환
        all_time_data = await get_portfolio_attribution_all_time(portfolio_id, AssetFilter.ALL, db)
        
        # 레거시 형식으로 변환
        asset_class_attributions = []
        for ac in all_time_data.asset_class_contributions:
            asset_class_attributions.append(AssetClassAttributionResponse(
                asset_class=ac.asset_class,
                weight=ac.avg_weight,
                return_contribution=ac.contribution,
                total_contribution=ac.contribution
            ))
        
        top_contributors = []
        for asset in all_time_data.top_contributors[:5]:
            top_contributors.append(AssetAttributionResponse(
                asset_id=asset.asset_id,
                ticker=asset.ticker,
                name=asset.name,
                weight=asset.avg_weight,
                return_contribution=asset.contribution,
                total_contribution=asset.contribution
            ))
        
        return AttributionResponse(
            asset_class_attributions=asset_class_attributions,
            top_contributors=top_contributors,
            period=period,
            start_date=all_time_data.start_date,
            end_date=all_time_data.end_date
        )
        
    except Exception as e:
        print(f"Error in get_portfolio_attribution_legacy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

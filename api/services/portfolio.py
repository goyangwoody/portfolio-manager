"""
Portfolio overview and holdings services
"""
from typing import List, Optional
from datetime import date
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database import get_db
from utils import safe_float
from schemas import (
    PortfoliosResponse, PortfolioListResponse, PortfolioSummaryResponse,
    PortfolioHoldingsResponse, AssetHolding, NavChartDataPoint,
    AssetDetailResponse, TimePeriod
)
from src.pm.db.models import (
    Portfolio, PortfolioNavDaily, PortfolioPositionDaily, Asset, Price
)

def calculate_sharpe_ratio(nav_history: List[PortfolioNavDaily]) -> Optional[float]:
    """
    NAV 히스토리를 기반으로 샤프 비율을 계산합니다.
    
    Args:
        nav_history: NAV 일별 데이터 리스트
    
    Returns:
        샤프 비율 또는 None (계산 불가능한 경우)
    """
    print(f"[DEBUG] calculate_sharpe_ratio: Received {len(nav_history)} NAV records")
    
    if len(nav_history) < 2:
        print(f"[DEBUG] Not enough NAV records: {len(nav_history)}")
        return None
    
    try:
        # 무위험 수익률 고정값 사용 (연율 2.5%)
        risk_free_rate = 0.025
        
        # NAV 값들을 추출하고 일별 수익률 계산
        nav_values = []
        for nav in nav_history:
            nav_val = safe_float(nav.nav)
            if nav_val is not None and nav_val > 0:
                nav_values.append(nav_val)
            else:
                print(f"[DEBUG] Invalid NAV value: {nav_val} on {nav.as_of_date}")
        
        print(f"[DEBUG] Valid NAV values: {len(nav_values)}")
        print(f"[DEBUG] First 5 NAV values: {nav_values[:5]}")
        print(f"[DEBUG] Last 5 NAV values: {nav_values[-5:]}")
        
        if len(nav_values) < 2:
            print(f"[DEBUG] Not enough valid NAV values: {len(nav_values)}")
            return None
        
        daily_returns = []
        
        for i in range(1, len(nav_values)):
            prev_nav = nav_values[i-1]
            curr_nav = nav_values[i]
            
            if prev_nav > 0 and curr_nav > 0:
                daily_return = (curr_nav - prev_nav) / prev_nav
                daily_returns.append(daily_return)
                if len(daily_returns) <= 5:  # 처음 몇 개만 로그
                    print(f"[DEBUG] Day {i}: {prev_nav:.4f} -> {curr_nav:.4f} = {daily_return:.6f}")
        
        print(f"[DEBUG] Daily returns calculated: {len(daily_returns)} returns")
        if len(daily_returns) > 0:
            print(f"[DEBUG] Sample daily returns: {daily_returns[:5]}")
        
        if len(daily_returns) < 2:  # 최소 2일 데이터로 완화
            print(f"[DEBUG] Not enough daily returns: {len(daily_returns)} < 2")
            return None
            
        returns_array = np.array(daily_returns)
        print(f"[DEBUG] Returns array - Mean: {np.mean(returns_array):.6f}, Std: {np.std(returns_array):.6f}")
        
        # 일일 무위험수익률
        daily_risk_free_rate = risk_free_rate / 252
        print(f"[DEBUG] Daily risk-free rate: {daily_risk_free_rate:.6f}")
        
        # 초과 수익률 계산
        excess_returns = returns_array - daily_risk_free_rate
        print(f"[DEBUG] Excess returns - Mean: {np.mean(excess_returns):.6f}")
        
        # 샤프 비율 계산 (연환산)
        std_returns = np.std(returns_array)
        if std_returns > 0:
            sharpe_ratio = np.mean(excess_returns) / std_returns * np.sqrt(252)
            print(f"[DEBUG] Calculated Sharpe ratio: {sharpe_ratio}")
            return float(sharpe_ratio)
        else:
            print(f"[DEBUG] Zero standard deviation")
            return 0.0
            
    except Exception as e:
        print(f"[ERROR] Error calculating Sharpe ratio: {e}")
        import traceback
        traceback.print_exc()
        return None

async def get_portfolios_service(
    include_kpi: bool = True,
    include_chart: bool = False,
    portfolio_type: Optional[str] = None,
    db: Session = None
) -> PortfoliosResponse:
    """
    포트폴리오 목록 조회 (Overview 페이지용)
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
                
                # 샤프 비율 계산
                print(f"[DEBUG] Portfolio {portfolio.id}: NAV history length = {len(nav_history)}")
                sharpe_ratio = calculate_sharpe_ratio(nav_history)
                print(f"[DEBUG] Portfolio {portfolio.id}: Calculated Sharpe ratio = {sharpe_ratio}")
                
                chart_data = []
                if nav_history:
                    for nav_record in nav_history:
                        chart_data.append(NavChartDataPoint(
                            date=nav_record.as_of_date,
                            nav=safe_float(nav_record.nav) or 0.0
                        ))
                
                portfolio_with_chart = {
                    "id": portfolio.id,
                    "name": portfolio.name,
                    "currency": portfolio.currency,
                    "total_return": total_return,
                    "sharpe_ratio": sharpe_ratio,
                    "nav": nav,
                    "cash_ratio": cash_ratio,
                    "chart_data": chart_data
                }
                
                portfolio_summaries.append(portfolio_with_chart)
            else:
                # 샤프 비율 계산을 위한 NAV 히스토리 조회
                nav_history = db.query(PortfolioNavDaily).filter(
                    PortfolioNavDaily.portfolio_id == portfolio.id
                ).order_by(PortfolioNavDaily.as_of_date).all()
                
                print(f"[DEBUG] Portfolio {portfolio.id}: NAV history length = {len(nav_history)}")
                sharpe_ratio = calculate_sharpe_ratio(nav_history)
                print(f"[DEBUG] Portfolio {portfolio.id}: Calculated Sharpe ratio = {sharpe_ratio}")
                
                portfolio_summary = PortfolioSummaryResponse(
                    id=portfolio.id,
                    name=portfolio.name,
                    currency=portfolio.currency,
                    total_return=total_return,
                    sharpe_ratio=sharpe_ratio,
                    nav=nav,
                    cash_ratio=cash_ratio
                )
                
                portfolio_summaries.append(portfolio_summary)
        
        return PortfoliosResponse(portfolios=portfolio_summaries)
        
    except Exception as e:
        print(f"Error in get_portfolios_service: {e}")
        raise e

async def get_portfolio_holdings_service(
    portfolio_id: int,
    as_of_date: Optional[date] = None,
    db: Session = None
) -> PortfolioHoldingsResponse:
    """포트폴리오 보유 자산 현황 조회 (Assets 페이지용)"""
    try:
        # 기준일 설정
        if not as_of_date:
            latest_position = db.query(PortfolioPositionDaily).filter(
                PortfolioPositionDaily.portfolio_id == portfolio_id
            ).order_by(desc(PortfolioPositionDaily.as_of_date)).first()
            
            if not latest_position:
                raise ValueError("No holdings data found")
            
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
            
            # 일일 변동률 계산
            day_change = 0.0
            if latest_price and latest_price.previous_close:
                day_change = ((current_price - latest_price.previous_close) / latest_price.previous_close) * 100
            
            holding = AssetHolding(
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
        
        # 현금 잔고 조회
        latest_nav = db.query(PortfolioNavDaily).filter(
            and_(
                PortfolioNavDaily.portfolio_id == portfolio_id,
                PortfolioNavDaily.as_of_date == as_of_date
            )
        ).first()
        
        nav_value = safe_float(latest_nav.nav) if latest_nav else total_market_value
        cash_balance = max(0, nav_value - total_market_value)
        
        return PortfolioHoldingsResponse(
            holdings=holdings,
            total_market_value=total_market_value,
            cash_balance=cash_balance,
            as_of_date=as_of_date
        )
        
    except Exception as e:
        print(f"Error in get_portfolio_holdings_service: {e}")
        raise e

async def get_asset_detail_service(
    portfolio_id: int,
    asset_id: int,
    period: TimePeriod = TimePeriod.INCEPTION,
    db: Session = None
) -> AssetDetailResponse:
    """개별 자산 상세 정보 조회 (Assets 페이지 디테일 시트용)"""
    try:
        # 자산 기본 정보
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError("Asset not found")
        
        from services.performance import parse_date_range
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
            asset_id=asset.id,
            ticker=asset.ticker or "",
            name=asset.name or asset.ticker or f"Asset_{asset.id}",
            asset_class=asset.asset_class or "Unknown",
            region=getattr(asset, "region", "unknown"),
            current_allocation=0.0,  # 계산 필요
            current_price=current_price,
            nav_return=cumulative_return,
            twr_contribution=0.0,  # 계산 필요
            price_performance=[
                {
                    "date": p.date,
                    "performance": ((safe_float(p.close) / safe_float(price_history[0].close)) - 1) * 100 
                    if price_history and price_history[0].close else 0.0
                } for p in price_history
            ]
        )
        
    except Exception as e:
        print(f"Error in get_asset_detail_service: {e}")
        raise e

# TODO: Risk & Allocation 서비스 구현 필요
# async def get_risk_and_allocation_service(
#     portfolio_id: int,
#     period: TimePeriod = TimePeriod.INCEPTION,
#     db: Session = None
# ):
#     """포트폴리오 리스크 및 배분 현황 조회 (Risk & Allocation 페이지용) - 현재 미구현"""
#     pass

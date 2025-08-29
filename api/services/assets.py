"""
Asset-related business logic and data processing
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, or_, func
from datetime import date
from typing import Optional, List
from schemas.holdings import CurrentHolding
from schemas.assets import AssetInfo
from schemas.common import AssetFilter

async def get_portfolio_assets_service(
    portfolio_id: int,
    as_of_date: Optional[date],
    asset_filter: AssetFilter,
    sort_by: str,
    sort_direction: str,
    search: Optional[str],
    db: Session
) -> List[CurrentHolding]:
    """포트폴리오 자산 목록 조회 서비스"""
    
    # 실제 DB 모델 import (동적 import로 순환 참조 방지)
    from src.pm.db.models import PortfolioPositionDaily, Asset, Portfolio
    
    # 포트폴리오 존재 확인
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise Exception("Portfolio not found")
    
    # 기준일 설정 (기본값: 최신일)
    if not as_of_date:
        latest_date = db.query(func.max(PortfolioPositionDaily.as_of_date)).filter(
            PortfolioPositionDaily.portfolio_id == portfolio_id
        ).scalar()
        as_of_date = latest_date or date.today()
    
    # 기본 쿼리 구성
    query = db.query(
        PortfolioPositionDaily,
        Asset
    ).join(
        Asset, PortfolioPositionDaily.asset_id == Asset.id
    ).filter(
        and_(
            PortfolioPositionDaily.portfolio_id == portfolio_id,
            PortfolioPositionDaily.as_of_date == as_of_date,
            PortfolioPositionDaily.quantity > 0  # 보유 수량이 있는 자산만
        )
    )
    
    # 자산 필터 적용
    if asset_filter == AssetFilter.DOMESTIC:
        query = query.filter(Asset.region == "domestic")
    elif asset_filter == AssetFilter.FOREIGN:
        query = query.filter(Asset.region == "foreign")
    
    # 검색어 적용
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Asset.name).like(search_term),
                func.lower(Asset.ticker).like(search_term)
            )
        )
    
    # 정렬 적용
    sort_column = None
    if sort_by == "name":
        sort_column = Asset.name
    elif sort_by == "avgPrice":
        sort_column = PortfolioPositionDaily.average_cost
    elif sort_by == "currentPrice":
        sort_column = PortfolioPositionDaily.unit_price
    elif sort_by == "marketValue":
        sort_column = PortfolioPositionDaily.market_value
    elif sort_by == "dayChange":
        # 일일 변동률은 계산 필요 (예시)
        sort_column = PortfolioPositionDaily.unit_price
    elif sort_by == "totalReturn":
        # 총 수익률은 계산 필요
        sort_column = PortfolioPositionDaily.market_value
    
    if sort_column is not None:
        if sort_direction == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    # 결과 조회
    results = query.all()
    
    # CurrentHolding 객체로 변환
    holdings = []
    for position, asset in results:
        # 수익률 계산 (예시)
        unrealized_pnl = position.market_value - (position.quantity * position.average_cost)
        unrealized_pnl_pct = (unrealized_pnl / (position.quantity * position.average_cost)) * 100 if position.average_cost > 0 else 0
        
        # 일일 변동률 계산 (예시 - 실제로는 이전 날짜와 비교 필요)
        day_change = 0.0  # TODO: 실제 계산 로직 구현
        
        holding = CurrentHolding(
            asset_id=asset.id,
            ticker=asset.ticker,
            name=asset.name,
            asset_class=asset.asset_class or "Unknown",
            region=asset.region,
            quantity=float(position.quantity),
            unit_price=float(position.unit_price),
            market_value=float(position.market_value),
            average_cost=float(position.average_cost),
            unrealized_pnl=float(unrealized_pnl),
            unrealized_pnl_pct=float(unrealized_pnl_pct),
            weight=float(position.weight) if position.weight else 0.0
        )
        holdings.append(holding)
    
    return holdings

async def get_asset_detail_service(
    portfolio_id: int,
    asset_id: int,
    as_of_date: Optional[date],
    db: Session
) -> CurrentHolding:
    """개별 자산 상세 정보 조회 서비스"""
    
    from src.pm.db.models import PortfolioPositionDaily, Asset
    
    # 기준일 설정
    if not as_of_date:
        latest_date = db.query(func.max(PortfolioPositionDaily.as_of_date)).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.asset_id == asset_id
            )
        ).scalar()
        as_of_date = latest_date or date.today()
    
    # 자산과 포지션 정보 조회
    result = db.query(
        PortfolioPositionDaily,
        Asset
    ).join(
        Asset, PortfolioPositionDaily.asset_id == Asset.id
    ).filter(
        and_(
            PortfolioPositionDaily.portfolio_id == portfolio_id,
            PortfolioPositionDaily.asset_id == asset_id,
            PortfolioPositionDaily.as_of_date == as_of_date
        )
    ).first()
    
    if not result:
        raise Exception("Asset not found in portfolio")
    
    position, asset = result
    
    # 수익률 계산
    unrealized_pnl = position.market_value - (position.quantity * position.average_cost)
    unrealized_pnl_pct = (unrealized_pnl / (position.quantity * position.average_cost)) * 100 if position.average_cost > 0 else 0
    
    return CurrentHolding(
        asset_id=asset.id,
        ticker=asset.ticker,
        name=asset.name,
        asset_class=asset.asset_class or "Unknown",
        region=asset.region,
        quantity=float(position.quantity),
        unit_price=float(position.unit_price),
        market_value=float(position.market_value),
        average_cost=float(position.average_cost),
        unrealized_pnl=float(unrealized_pnl),
        unrealized_pnl_pct=float(unrealized_pnl_pct),
        weight=float(position.weight) if position.weight else 0.0
    )

async def get_asset_price_history_service(
    portfolio_id: int,
    asset_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    interval: str,
    db: Session
):
    """자산 가격 히스토리 조회 서비스"""
    
    from src.pm.db.models import AssetPrice
    
    # 기본 기간 설정 (1년)
    if not end_date:
        end_date = date.today()
    if not start_date:
        from datetime import timedelta
        start_date = end_date - timedelta(days=365)
    
    # 가격 히스토리 조회
    query = db.query(AssetPrice).filter(
        and_(
            AssetPrice.asset_id == asset_id,
            AssetPrice.date >= start_date,
            AssetPrice.date <= end_date
        )
    ).order_by(AssetPrice.date)
    
    prices = query.all()
    
    # 응답 형식 변환
    price_data = []
    for price in prices:
        price_data.append({
            "date": price.date.isoformat(),
            "price": float(price.close_price),
            "normalized": 100.0  # TODO: 정규화 로직 구현
        })
    
    return {
        "data": price_data,
        "currency": "USD",  # TODO: 실제 통화 정보
        "interval": interval
    }

async def search_assets_service(
    query: str,
    limit: int,
    db: Session
) -> List[AssetInfo]:
    """전역 자산 검색 서비스"""
    
    from src.pm.db.models import Asset
    
    search_term = f"%{query.lower()}%"
    
    results = db.query(Asset).filter(
        or_(
            func.lower(Asset.name).like(search_term),
            func.lower(Asset.ticker).like(search_term)
        )
    ).limit(limit).all()
    
    assets = []
    for asset in results:
        assets.append(AssetInfo(
            asset_id=asset.id,
            ticker=asset.ticker,
            name=asset.name,
            asset_class=asset.asset_class or "Unknown",
            region=asset.region,
            currency=asset.currency
        ))
    
    return assets

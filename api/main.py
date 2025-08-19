import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

# 기존 모델 import
from src.pm.db.models import (
    SessionLocal, Portfolio, PortfolioPerformance, PortfolioAttribution, 
    PortfolioRiskMetrics, PortfolioSectorAllocation, Asset, PortfolioPositionDaily,
    PortfolioNavDaily, Price, AssetAttributionPeriodic, AssetClassAttributionPeriodic,
    AssetClassReturnDaily
)

app = FastAPI(title="PortfolioPulse API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5000"],
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

# Portfolio endpoints
@app.get("/api/portfolios")
async def get_portfolios(type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all portfolios"""
    print(f"API called: get_portfolios with type={type}")
    
    portfolios = db.query(Portfolio).all()
    print(f"Found {len(portfolios)} portfolios in database")
    
    if not portfolios:
        print("No portfolios found in database")
        return {"message": "No portfolios found in database", "data": []}
    
    result = []
    for portfolio in portfolios:
        # 최신 NAV 데이터 가져오기
        latest_nav = db.query(PortfolioNavDaily).filter(
            PortfolioNavDaily.portfolio_id == portfolio.id
        ).order_by(PortfolioNavDaily.as_of_date.desc()).first()
        
        # 최신 위험 지표 가져오기
        latest_risk = db.query(PortfolioRiskMetrics).filter(
            PortfolioRiskMetrics.portfolio_id == portfolio.id
        ).order_by(PortfolioRiskMetrics.date.desc()).first()
        
        # 최신 성과 데이터 가져오기
        latest_performance = db.query(PortfolioPerformance).filter(
            PortfolioPerformance.portfolio_id == portfolio.id
        ).order_by(PortfolioPerformance.date.desc()).first()
        
        # 총 수익률 계산 (초기 현금 대비 현재 NAV)
        total_return = 0.0
        if latest_nav and portfolio.initial_cash:
            total_return = ((float(latest_nav.nav) - float(portfolio.initial_cash)) / float(portfolio.initial_cash)) * 100
        
        portfolio_data = {
            "id": str(portfolio.id),
            "name": portfolio.name,
            "type": type or "domestic",  # 타입 구분이 없으면 기본값
            "currency": portfolio.currency,  # 포트폴리오 기준 통화
            "totalReturn": total_return,
            "sharpeRatio": float(latest_risk.sharpe_ratio) if latest_risk else 0.0,
            "nav": float(latest_nav.nav) if latest_nav else float(portfolio.cash_balance),
            "aum": float(latest_nav.nav) if latest_nav else float(portfolio.cash_balance),
            "volatility": float(latest_risk.volatility) if latest_risk else 0.0,
            "maxDrawdown": float(latest_risk.max_drawdown) if latest_risk else 0.0,
            "beta": float(latest_risk.beta) if latest_risk else 1.0,
            "lastUpdated": latest_nav.as_of_date.isoformat() if latest_nav else portfolio.created_at.isoformat(),
            "hasData": {
                "nav": latest_nav is not None,
                "risk": latest_risk is not None,
                "performance": latest_performance is not None
            }
        }
        result.append(portfolio_data)
    
    return result

@app.get("/api/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Get portfolio by ID"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == int(portfolio_id)).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # 최신 성과 및 위험 지표 포함
    latest_risk = db.query(PortfolioRiskMetrics).filter(
        PortfolioRiskMetrics.portfolio_id == portfolio.id
    ).order_by(PortfolioRiskMetrics.date.desc()).first()
    
    latest_performance = db.query(PortfolioPerformance).filter(
        PortfolioPerformance.portfolio_id == portfolio.id
    ).order_by(PortfolioPerformance.date.desc()).first()
    
    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "type": "domestic",
        "currency": portfolio.currency,  # 포트폴리오 기준 통화
        "totalReturn": float(latest_performance.daily_return) if latest_performance else 0.0,
        "sharpeRatio": float(latest_risk.sharpe_ratio) if latest_risk else 0.0,
        "nav": float(latest_performance.portfolio_value) if latest_performance else float(portfolio.cash_balance),
        "aum": float(portfolio.cash_balance),
        "volatility": float(latest_risk.volatility) if latest_risk else 0.0,
        "maxDrawdown": float(latest_risk.max_drawdown) if latest_risk else 0.0,
        "beta": float(latest_risk.beta) if latest_risk else 1.0,
        "lastUpdated": latest_performance.date.isoformat() if latest_performance else portfolio.created_at.isoformat()
    }

@app.get("/api/portfolios/{portfolio_id}/performance")
async def get_performance_data(portfolio_id: str, db: Session = Depends(get_db)):
    """Get performance data for a portfolio"""
    # 먼저 PortfolioPerformance 테이블에서 데이터 조회
    performance_data = db.query(PortfolioPerformance).filter(
        PortfolioPerformance.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioPerformance.date).all()
    
    if performance_data:
        return [
            {
                "id": str(perf.id),
                "portfolioId": str(perf.portfolio_id),
                "date": perf.date.isoformat(),
                "portfolioValue": float(perf.portfolio_value),
                "benchmarkValue": float(perf.benchmark_value),
                "dailyReturn": float(perf.daily_return) if perf.daily_return else None,
                "monthlyReturn": float(perf.monthly_return) if perf.monthly_return else None,
                "quarterlyReturn": float(perf.quarterly_return) if perf.quarterly_return else None
            }
            for perf in performance_data
        ]
    
    # 없으면 PortfolioNavDaily에서 NAV 데이터로 성과 차트 생성
    nav_data = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioNavDaily.as_of_date).limit(252).all()  # 최근 1년
    
    if nav_data:
        # NAV 데이터를 성과 데이터로 변환
        performance_list = []
        for nav in nav_data:
            # 벤치마크 가치는 샘플 데이터로 대체 (실제 벤치마크 로직 구현 필요)
            benchmark_value = float(nav.nav) * 0.95  # 간단한 벤치마크 시뮬레이션
            
            performance_list.append({
                "id": str(nav.id),
                "portfolioId": str(nav.portfolio_id),
                "date": nav.as_of_date.isoformat(),
                "portfolioValue": float(nav.nav),
                "benchmarkValue": benchmark_value,
                "dailyReturn": None,
                "monthlyReturn": None,
                "quarterlyReturn": None
            })
        
        return performance_list
    
    # 데이터가 없으면 명확한 메시지와 함께 빈 배열 반환
    return {"message": "No performance data found for this portfolio", "data": []}

@app.get("/api/portfolios/{portfolio_id}/attribution")
async def get_attribution_data(portfolio_id: str, db: Session = Depends(get_db)):
    """Get attribution data for a portfolio"""
    # 먼저 기존 PortfolioAttribution 테이블에서 데이터 조회
    attribution_data = db.query(PortfolioAttribution).filter(
        PortfolioAttribution.portfolio_id == int(portfolio_id)
    ).all()
    
    # 기존 데이터가 있으면 반환
    if attribution_data:
        return [
            {
                "id": str(attr.id),
                "portfolioId": str(attr.portfolio_id),
                "assetClass": attr.asset_class,
                "allocation": float(attr.allocation),
                "contribution": float(attr.contribution)
            }
            for attr in attribution_data
        ]
    
    # 없으면 AssetClassAttributionPeriodic에서 최신 데이터 조회
    asset_class_attributions = db.query(AssetClassAttributionPeriodic).filter(
        AssetClassAttributionPeriodic.portfolio_id == int(portfolio_id)
    ).order_by(AssetClassAttributionPeriodic.start_date.desc()).limit(10).all()
    
    if asset_class_attributions:
        return [
            {
                "id": str(attr.id),
                "portfolioId": str(attr.portfolio_id),
                "assetClass": attr.asset_class,
                "allocation": float(attr.allocation),
                "contribution": float(attr.contribution)
            }
            for attr in asset_class_attributions
        ]
    
    # 데이터가 없으면 샘플 데이터 반환
    return [
        {"id": "1", "portfolioId": portfolio_id, "assetClass": "Equities", "allocation": 60.0, "contribution": 2.5},
        {"id": "2", "portfolioId": portfolio_id, "assetClass": "Bonds", "allocation": 30.0, "contribution": 0.8},
        {"id": "3", "portfolioId": portfolio_id, "assetClass": "Alternatives", "allocation": 10.0, "contribution": 0.3}
    ]

@app.get("/api/portfolios/{portfolio_id}/risk")
async def get_risk_metrics(portfolio_id: str, db: Session = Depends(get_db)):
    """Get risk metrics for a portfolio"""
    risk_metrics = db.query(PortfolioRiskMetrics).filter(
        PortfolioRiskMetrics.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioRiskMetrics.date.desc()).first()
    
    if not risk_metrics:
        raise HTTPException(status_code=404, detail="Risk metrics not found")
    
    return {
        "id": str(risk_metrics.id),
        "portfolioId": str(risk_metrics.portfolio_id),
        "var95": float(risk_metrics.var_95),
        "var99": float(risk_metrics.var_99),
        "expectedShortfall": float(risk_metrics.expected_shortfall),
        "trackingError": float(risk_metrics.tracking_error),
        "informationRatio": float(risk_metrics.information_ratio),
        "sharpeRatio": float(risk_metrics.sharpe_ratio),
        "volatility": float(risk_metrics.volatility),
        "maxDrawdown": float(risk_metrics.max_drawdown),
        "beta": float(risk_metrics.beta)
    }

@app.get("/api/portfolios/{portfolio_id}/sectors")
async def get_sector_allocations(portfolio_id: str, db: Session = Depends(get_db)):
    """Get sector allocations for a portfolio"""
    # 먼저 PortfolioSectorAllocation 테이블에서 데이터 조회
    sector_data = db.query(PortfolioSectorAllocation).filter(
        PortfolioSectorAllocation.portfolio_id == int(portfolio_id)
    ).all()
    
    if sector_data:
        return [
            {
                "id": str(sector.id),
                "portfolioId": str(sector.portfolio_id),
                "sector": sector.sector,
                "allocation": float(sector.allocation),
                "contribution": float(sector.contribution)
            }
            for sector in sector_data
        ]
    
    # 없으면 현재 포지션에서 asset_class별로 집계
    latest_date = db.query(PortfolioPositionDaily.as_of_date).filter(
        PortfolioPositionDaily.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioPositionDaily.as_of_date.desc()).first()
    
    if not latest_date:
        return []
    
    # Get total portfolio value
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioNavDaily.as_of_date.desc()).first()
    
    total_value = float(latest_nav.nav) if latest_nav else 1000000000.0
    
    # Get positions and group by asset class
    positions = db.query(PortfolioPositionDaily, Asset).join(
        Asset, PortfolioPositionDaily.asset_id == Asset.id
    ).filter(
        PortfolioPositionDaily.portfolio_id == int(portfolio_id),
        PortfolioPositionDaily.as_of_date == latest_date[0],
        PortfolioPositionDaily.quantity > 0
    ).all()
    
    sector_allocations = {}
    for position, asset in positions:
        sector = asset.asset_class or "Unknown"
        market_value = float(position.market_value)
        
        if sector not in sector_allocations:
            sector_allocations[sector] = {"value": 0.0, "count": 0}
        
        sector_allocations[sector]["value"] += market_value
        sector_allocations[sector]["count"] += 1
    
    # Convert to API format
    result = []
    for i, (sector, data) in enumerate(sector_allocations.items()):
        allocation = (data["value"] / total_value) * 100
        result.append({
            "id": str(i + 1),
            "portfolioId": portfolio_id,
            "sector": sector,
            "allocation": allocation,
            "contribution": 0.0  # Would need performance calculation
        })
    
    return result

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "PortfolioPulse API is running"}

# Database status check
@app.get("/api/database/status")
async def get_database_status(db: Session = Depends(get_db)):
    """Check database status and data availability"""
    status = {
        "portfolios": db.query(Portfolio).count(),
        "nav_records": db.query(PortfolioNavDaily).count(),
        "position_records": db.query(PortfolioPositionDaily).count(),
        "assets": db.query(Asset).count(),
        "prices": db.query(Price).count(),
        "performance_records": db.query(PortfolioPerformance).count(),
        "risk_metrics": db.query(PortfolioRiskMetrics).count(),
        "attribution_records": db.query(PortfolioAttribution).count(),
    }
    
    status["has_data"] = any(count > 0 for count in status.values())
    
    return status

# Holdings endpoint
@app.get("/api/portfolios/{portfolio_id}/holdings")
async def get_holdings(portfolio_id: str, type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get holdings for a portfolio"""
    # Get latest NAV for portfolio total calculation
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioNavDaily.as_of_date.desc()).first()
    
    total_portfolio_value = float(latest_nav.nav) if latest_nav else 1000000000.0
    
    # Get latest positions for the portfolio
    latest_date = db.query(PortfolioPositionDaily.as_of_date).filter(
        PortfolioPositionDaily.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioPositionDaily.as_of_date.desc()).first()
    
    if latest_date:
        positions = db.query(PortfolioPositionDaily).filter(
            PortfolioPositionDaily.portfolio_id == int(portfolio_id),
            PortfolioPositionDaily.as_of_date == latest_date[0],
            PortfolioPositionDaily.quantity > 0
        ).all()
    else:
        positions = []
    
    holdings = []
    for position in positions:
        asset = db.query(Asset).filter(Asset.id == position.asset_id).first()
        if asset:
            # Calculate weight as percentage of total portfolio
            weight = (float(position.market_value) / total_portfolio_value) * 100
            
            # Get asset attribution data for return calculation
            asset_attribution = db.query(AssetAttributionPeriodic).filter(
                AssetAttributionPeriodic.portfolio_id == int(portfolio_id),
                AssetAttributionPeriodic.asset_id == position.asset_id
            ).order_by(AssetAttributionPeriodic.start_date.desc()).first()
            
            asset_return = float(asset_attribution.asset_return) if asset_attribution else 0.0
            contribution = float(asset_attribution.contribution) if asset_attribution else 0.0
            
            holdings.append({
                "id": str(position.id),
                "portfolioId": str(position.portfolio_id),
                "name": asset.name or asset.ticker,
                "weight": weight,
                "return": asset_return,
                "contribution": contribution,
                "type": "contributor" if contribution > 0 else "detractor"
            })
    
    # Sort by market value descending
    holdings.sort(key=lambda x: x["weight"], reverse=True)
    
    return holdings

# Benchmarks endpoint
@app.get("/api/portfolios/{portfolio_id}/benchmarks")
async def get_benchmarks(portfolio_id: str, db: Session = Depends(get_db)):
    """Get benchmarks for a portfolio"""
    # For now, return sample benchmark data
    # This should be implemented based on your benchmark data structure
    return [
        {
            "id": "1",
            "portfolioId": portfolio_id,
            "name": "KOSPI 200",
            "value": "2450.50",
            "change": "1.2",
            "changePercent": "0.05"
        },
        {
            "id": "2", 
            "portfolioId": portfolio_id,
            "name": "S&P 500",
            "value": "4750.80",
            "change": "15.4",
            "changePercent": "0.32"
        }
    ]

@app.get("/api/portfolios/{portfolio_id}/assets")
async def get_assets(portfolio_id: str, db: Session = Depends(get_db)):
    """Get assets for a portfolio"""
    # Get latest NAV for portfolio total calculation
    latest_nav = db.query(PortfolioNavDaily).filter(
        PortfolioNavDaily.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioNavDaily.as_of_date.desc()).first()
    
    # Get latest date for positions
    latest_date = db.query(PortfolioPositionDaily.as_of_date).filter(
        PortfolioPositionDaily.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioPositionDaily.as_of_date.desc()).first()
    
    if not latest_date:
        return {"message": "No position data found for this portfolio", "data": []}
    
    total_portfolio_value = float(latest_nav.nav) if latest_nav else 1000000000.0
    
    # Get latest positions
    positions = db.query(PortfolioPositionDaily).filter(
        PortfolioPositionDaily.portfolio_id == int(portfolio_id),
        PortfolioPositionDaily.as_of_date == latest_date[0],
        PortfolioPositionDaily.quantity > 0
    ).all()
    
    if not positions:
        return {"message": "No assets found in this portfolio", "data": []}
    
    assets = []
    for position in positions:
        asset = db.query(Asset).filter(Asset.id == position.asset_id).first()
        if asset:
            # Get latest price
            latest_price = db.query(Price).filter(
                Price.asset_id == position.asset_id
            ).order_by(Price.date.desc()).first()
            
            current_price = float(latest_price.close) if latest_price else float(position.avg_price)
            
            # Calculate P&L
            unrealized_pnl = (current_price - float(position.avg_price)) * float(position.quantity)
            total_return = ((current_price - float(position.avg_price)) / float(position.avg_price)) * 100
            weight = (float(position.market_value) / total_portfolio_value) * 100
            
            assets.append({
                "id": str(asset.id),
                "portfolioId": str(position.portfolio_id),
                "name": asset.name or asset.ticker,
                "ticker": asset.ticker,
                "quantity": float(position.quantity),
                "avgPrice": float(position.avg_price),
                "currentPrice": current_price,
                "marketValue": float(position.market_value),
                "unrealizedPnL": unrealized_pnl,
                "realizedPnL": 0.0,  # Would need transaction history calculation
                "totalReturn": total_return,
                "weight": weight,
                "sector": asset.asset_class or "Unknown"
            })
    
    # Sort by market value descending
    assets.sort(key=lambda x: x["marketValue"], reverse=True)
    
    return assets

# Asset performance endpoint
@app.get("/api/assets/{asset_id}/performance")
async def get_asset_performance(asset_id: str, db: Session = Depends(get_db)):
    """Get performance data for an asset"""
    prices = db.query(Price).filter(
        Price.asset_id == int(asset_id)
    ).order_by(Price.date).limit(252).all()  # Last year of data
    
    performance_data = []
    for price in prices:
        performance_data.append({
            "id": str(price.id),
            "assetId": asset_id,
            "date": price.date.isoformat(),
            "price": float(price.close)
        })
    
    return performance_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

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
    PortfolioRiskMetrics, PortfolioSectorAllocation
)

app = FastAPI(title="PortfolioPulse API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
    portfolios = db.query(Portfolio).all()
    
    # 포트폴리오 목록을 프론트엔드 형식으로 변환
    result = []
    for portfolio in portfolios:
        # 최신 위험 지표 가져오기
        latest_risk = db.query(PortfolioRiskMetrics).filter(
            PortfolioRiskMetrics.portfolio_id == portfolio.id
        ).order_by(PortfolioRiskMetrics.date.desc()).first()
        
        # 현재 포트폴리오 가치 계산 (최신 성과 데이터에서)
        latest_performance = db.query(PortfolioPerformance).filter(
            PortfolioPerformance.portfolio_id == portfolio.id
        ).order_by(PortfolioPerformance.date.desc()).first()
        
        portfolio_data = {
            "id": str(portfolio.id),
            "name": portfolio.name,
            "type": type or "domestic",  # 기존 모델에 type이 없으면 기본값
            "totalReturn": float(latest_performance.daily_return) if latest_performance else 0.0,
            "sharpeRatio": float(latest_risk.sharpe_ratio) if latest_risk else 0.0,
            "nav": float(latest_performance.portfolio_value) if latest_performance else float(portfolio.cash_balance),
            "aum": float(portfolio.cash_balance),
            "volatility": float(latest_risk.volatility) if latest_risk else 0.0,
            "maxDrawdown": float(latest_risk.max_drawdown) if latest_risk else 0.0,
            "beta": float(latest_risk.beta) if latest_risk else 1.0,
            "lastUpdated": latest_performance.date.isoformat() if latest_performance else portfolio.created_at.isoformat()
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
    performance_data = db.query(PortfolioPerformance).filter(
        PortfolioPerformance.portfolio_id == int(portfolio_id)
    ).order_by(PortfolioPerformance.date).all()
    
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

@app.get("/api/portfolios/{portfolio_id}/attribution")
async def get_attribution_data(portfolio_id: str, db: Session = Depends(get_db)):
    """Get attribution data for a portfolio"""
    attribution_data = db.query(PortfolioAttribution).filter(
        PortfolioAttribution.portfolio_id == int(portfolio_id)
    ).all()
    
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
    sector_data = db.query(PortfolioSectorAllocation).filter(
        PortfolioSectorAllocation.portfolio_id == int(portfolio_id)
    ).all()
    
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

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "PortfolioPulse API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

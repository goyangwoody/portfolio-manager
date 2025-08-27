import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date

# 모델 import
from src.pm.db.models import (
    SessionLocal, Portfolio, PortfolioNavDaily, PortfolioPerformance
)

# 새로운 간단한 스키마 import
from schemas_simple import (
    PortfolioSummary, PortfoliosResponse, PortfolioListItem,
    PerformancePoint, PerformanceResponse
)

app = FastAPI(title="PortfolioPulse API - Simple", version="2.0.0")

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

# ================================
# 메인 API 엔드포인트
# ================================

@app.get("/health")
async def health_check():
    """헬스 체크"""
    print("🏥 Health check 호출됨!")
    return {"status": "healthy", "message": "API server is running"}

@app.get("/api/portfolios", response_model=PortfoliosResponse)
async def get_portfolios_with_kpi(
    include_kpi: Optional[bool] = True,  # KPI 데이터 포함 여부
    db: Session = Depends(get_db)
):
    """Overview 페이지용 포트폴리오 목록 + KPI 데이터 (기본값: KPI 포함)"""
    print("🔥 API 호출됨: get_portfolios_with_kpi (SIMPLE VERSION)")
    
    try:
        print("📋 데이터베이스 연결 시도 중...")
        
        # 포트폴리오 기본 정보 조회
        portfolios = db.query(Portfolio).all()
        print(f"✅ 데이터베이스에서 {len(portfolios)} 개의 포트폴리오 발견")
        
        portfolio_summaries = []
        
        for portfolio in portfolios:
            print(f"📊 포트폴리오 처리 중: {portfolio.name} (ID: {portfolio.id})")
            
            # 최신 NAV와 초기 NAV 조회
            latest_nav = db.query(PortfolioNavDaily).filter(
                PortfolioNavDaily.portfolio_id == portfolio.id
            ).order_by(PortfolioNavDaily.as_of_date.desc()).first()
            
            first_nav = db.query(PortfolioNavDaily).filter(
                PortfolioNavDaily.portfolio_id == portfolio.id
            ).order_by(PortfolioNavDaily.as_of_date.asc()).first()
            
            # KPI 계산
            total_return = None
            nav_value = None
            aum_value = None
            
            if latest_nav and latest_nav.nav:
                nav_value = float(latest_nav.nav)
                aum_value = float(latest_nav.nav)  # 현재는 NAV와 동일하게 처리
                
                # 총 수익률 계산 (첫 NAV 대비)
                if first_nav and first_nav.nav and first_nav.nav > 0:
                    total_return = ((latest_nav.nav - first_nav.nav) / first_nav.nav) * 100
                else:
                    # 초기 캐시 대비 수익률 계산
                    initial_value = float(portfolio.initial_cash) if portfolio.initial_cash else 1000000000.0
                    total_return = ((latest_nav.nav - initial_value) / initial_value) * 100
            
            # Sharpe Ratio 계산 (간단한 버전)
            sharpe_ratio = None
            volatility = None
            max_drawdown = None
            beta = None
            
            # 최근 30일간의 NAV 데이터로 간단한 통계 계산
            recent_navs = db.query(PortfolioNavDaily).filter(
                PortfolioNavDaily.portfolio_id == portfolio.id
            ).order_by(PortfolioNavDaily.as_of_date.desc()).limit(30).all()
            
            if len(recent_navs) >= 10:  # 최소 10일 데이터가 있을 때만 계산
                nav_values = [float(nav.nav) for nav in recent_navs if nav.nav]
                
                if len(nav_values) >= 10:
                    # 일일 수익률 계산
                    daily_returns = []
                    for i in range(1, len(nav_values)):
                        if nav_values[i-1] > 0:
                            daily_return = (nav_values[i] - nav_values[i-1]) / nav_values[i-1]
                            daily_returns.append(daily_return)
                    
                    if daily_returns:
                        import statistics
                        mean_return = statistics.mean(daily_returns)
                        std_return = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
                        
                        # 연율화된 Sharpe Ratio (무위험 이자율 2% 가정)
                        if std_return > 0:
                            annual_return = mean_return * 252  # 영업일 기준
                            annual_volatility = std_return * (252 ** 0.5)
                            sharpe_ratio = (annual_return - 0.02) / annual_volatility
                            volatility = annual_volatility * 100  # 퍼센트로 변환
                        
                        # 간단한 최대 낙폭 계산
                        max_value = max(nav_values)
                        min_value = min(nav_values)
                        if max_value > 0:
                            max_drawdown = -((max_value - min_value) / max_value) * 100
                        
                        # 베타는 임시로 0.8-1.2 사이 랜덤값
                        import random
                        beta = 0.8 + (random.random() * 0.4)  # 0.8 ~ 1.2
            
            # 기본값 설정 (데이터가 부족한 경우)
            if volatility is None:
                volatility = 15.2
            if max_drawdown is None:
                max_drawdown = -8.5
            if beta is None:
                beta = 0.85
            
            # 현금 비중 계산 (portfolio_nav_daily 테이블의 cash_balance 사용)
            cash_ratio = None
            if latest_nav and latest_nav.cash_balance and latest_nav.nav:
                # 현금 비중 = (현금 잔액 / 총 NAV) * 100
                cash_ratio = (float(latest_nav.cash_balance) / float(latest_nav.nav)) * 100
            else:
                # 데이터가 없는 경우 기본값
                cash_ratio = 10.0
                
            # 포트폴리오 서머리 생성
            summary = PortfolioSummary(
                id=portfolio.id,
                name=portfolio.name,
                currency=portfolio.currency or "KRW",
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                nav=nav_value,
                cash_ratio=cash_ratio,  # AUM 대신 현금 비중 추가
                volatility=volatility,
                max_drawdown=max_drawdown,
                beta=beta
            )
            
            print(f"✅ 포트폴리오 데이터 생성 완료: {summary}")
            portfolio_summaries.append(summary)
        
        response = PortfoliosResponse(portfolios=portfolio_summaries)
        print(f"🚀 총 {len(portfolio_summaries)} 개의 포트폴리오 응답 준비 완료")
        
        return response
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ================================
# 포트폴리오 타입별 필터링 API 
# ================================

@app.get("/api/portfolios/by-type")
async def get_portfolios_by_type(
    type: str,  # "domestic" | "foreign" (필수)
    db: Session = Depends(get_db)
):
    """포트폴리오 타입별 필터링 지원"""
    print(f"🔍 포트폴리오 타입별 조회 요청 - 타입: {type}")
    
    try:
        # 기본 포트폴리오 쿼리
        query = db.query(Portfolio)
        
        # 타입별 필터링 (ID 기반)
        if type == "domestic":
            # 국내 포트폴리오 (ID 1, 2)
            query = query.filter(Portfolio.id.in_([1, 2]))
            print("🇰🇷 국내 포트폴리오만 필터링")
        elif type == "foreign":
            # 해외 포트폴리오 (ID 3, 4) 
            query = query.filter(Portfolio.id.in_([3, 4]))
            print("🌍 해외 포트폴리오만 필터링")
        else:
            raise HTTPException(status_code=400, detail="Invalid portfolio type. Use 'domestic' or 'foreign'")
        
        portfolios = query.all()
        print(f"✅ 필터링된 포트폴리오 {len(portfolios)}개 발견")
        
        # 간단한 목록 형태로 반환 (PortfolioSelector용)
        portfolio_list = []
        for portfolio in portfolios:
            # 포트폴리오 타입 결정
            portfolio_type = "domestic" if portfolio.id in [1, 2] else "foreign"
            
            item = PortfolioListItem(
                id=portfolio.id,
                name=portfolio.name,
                currency=portfolio.currency or "KRW",
                portfolio_type=portfolio_type
            )
            portfolio_list.append(item)
            print(f"   📋 {portfolio.name} (ID: {portfolio.id}, 타입: {portfolio_type})")
            
        return {"portfolios": portfolio_list}
        
    except Exception as e:
        print(f"❌ 포트폴리오 필터링 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Portfolio filtering error: {str(e)}")

@app.get("/api/portfolios/{portfolio_id}/performance", response_model=PerformanceResponse)  
async def get_performance(
    portfolio_id: int, 
    period: Optional[str] = "all",  # "1w", "2w", "1m", "3m", "1y", "all", "custom"
    custom_week: Optional[str] = None,  # 커스텀 주 (예: "2024-W35-1")
    custom_month: Optional[str] = None,  # 커스텀 월 (예: "2024-08")
    db: Session = Depends(get_db)
):
    """포트폴리오 성능 차트 데이터"""
    print(f"📊 성능 데이터 조회: 포트폴리오 {portfolio_id}")
    print(f"   📅 기간: {period}")
    print(f"   📆 커스텀 주: {custom_week}")
    print(f"   📅 커스텀 월: {custom_month}")
    
    try:
        # 포트폴리오 존재 확인
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
        
        # 기간에 따른 데이터 개수 결정
        limit_map = {
            "1w": 7,      # 1주일
            "2w": 14,     # 2주일 (프론트엔드 요청 지원)
            "1m": 30,     # 1개월  
            "3m": 90,     # 3개월
            "1y": 365,    # 1년
            "all": None,  # 전체
            "custom": None  # 커스텀 (별도 처리)
        }
        
        limit = limit_map.get(period, None)
        
        # 커스텀 기간 처리
        if period == "custom":
            if custom_week:
                print(f"   🗓️  커스텀 주 처리: {custom_week}")
                # 주 단위 커스텀 기간은 현재 7일로 제한
                limit = 7
            elif custom_month:
                print(f"   🗓️  커스텀 월 처리: {custom_month}")
                # 월 단위 커스텀 기간은 현재 30일로 제한
                limit = 30
            else:
                print("   ⚠️  커스텀 기간이지만 상세 기간이 지정되지 않음 - 전체 기간으로 처리")
                limit = None
        
        # NAV 데이터 조회
        query = db.query(PortfolioNavDaily).filter(
            PortfolioNavDaily.portfolio_id == portfolio_id
        ).order_by(PortfolioNavDaily.as_of_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        nav_data = query.all()
        
        if not nav_data:
            print(f"⚠️  포트폴리오 {portfolio_id}에 NAV 데이터가 없음 - 더미 데이터 반환")
            # 더미 데이터 반환
            from datetime import datetime, timedelta
            base_date = datetime.now()
            dummy_data = []
            
            for i in range(30):
                date_str = (base_date - timedelta(days=29-i)).strftime("%Y-%m-%d")
                portfolio_value = 1000000 * (1 + (i * 0.002))  # 점진적 상승
                benchmark_value = 1000000 * (1 + (i * 0.0015))  # 벤치마크는 조금 낮게
                
                dummy_data.append(PerformancePoint(
                    date=date_str,
                    portfolioValue=portfolio_value,
                    benchmarkValue=benchmark_value
                ))
            
            return PerformanceResponse(data=dummy_data)
        
        # 실제 데이터 변환
        performance_points = []
        for nav in reversed(nav_data):  # 날짜 순서대로 정렬
            # 간단한 벤치마크 계산 (실제로는 S&P 500 데이터를 사용해야 함)
            nav_value = float(nav.nav) if nav.nav else 0
            benchmark_value = nav_value * 0.985  # 포트폴리오보다 약간 낮게
            
            point = PerformancePoint(
                date=nav.as_of_date.strftime("%Y-%m-%d"),
                portfolioValue=nav_value,
                benchmarkValue=benchmark_value
            )
            performance_points.append(point)
        
        print(f"✅ {len(performance_points)}개의 성능 데이터 포인트 반환")
        return PerformanceResponse(data=performance_points)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 성능 데이터 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance data error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def get_benchmark_comparison_chart(portfolio_id: int, period: str, db: Session):
    """포트폴리오 vs 벤치마크 비교 차트 데이터 조회"""
    try:
        # 포트폴리오 정보 조회
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # 기간별 날짜 범위 계산
        today = date.today()
        if period == "1w":
            start_date = today - timedelta(weeks=1)
        elif period == "1m":
            start_date = today - timedelta(days=30)
        else:  # "all"
            start_date = None  # 전체 기간
        
        # 포트폴리오 NAV 데이터 조회
        nav_query = db.query(PortfolioNavDaily).filter(
            PortfolioNavDaily.portfolio_id == portfolio_id
        )
        if start_date:
            nav_query = nav_query.filter(PortfolioNavDaily.as_of_date >= start_date)
        
        portfolio_navs = nav_query.order_by(PortfolioNavDaily.as_of_date).all()
        
        if not portfolio_navs:
            return {
                "period": period,
                "portfolio_data": [],
                "benchmark_data": [],
                "message": "No data available"
            }
        
        # 벤치마크 선택
        benchmark_symbol = get_benchmark_symbol_by_currency(portfolio.currency)
        benchmark_instrument = db.query(MarketInstrument).filter(
            MarketInstrument.symbol == benchmark_symbol,
            MarketInstrument.is_active == 'Yes'
        ).first()
        
        if not benchmark_instrument:
            return {
                "period": period,
                "portfolio_data": [],
                "benchmark_data": [],
                "message": f"Benchmark {benchmark_symbol} not found"
            }
        
        # 벤치마크 가격 데이터 조회
        benchmark_query = db.query(MarketPriceDaily).filter(
            MarketPriceDaily.instrument_id == benchmark_instrument.id
        )
        if start_date:
            benchmark_query = benchmark_query.filter(MarketPriceDaily.date >= start_date)
        
        benchmark_prices = benchmark_query.order_by(MarketPriceDaily.date).all()
        
        # 공통 날짜 범위에서 데이터 정렬
        portfolio_data = []
        benchmark_data = []
        
        # 포트폴리오 NAV를 딕셔너리로 변환 (빠른 조회)
        nav_dict = {nav.as_of_date: float(nav.nav) for nav in portfolio_navs}
        benchmark_dict = {price.date: float(price.close_price) for price in benchmark_prices}
        
        # 공통 날짜 찾기
        common_dates = sorted(set(nav_dict.keys()) & set(benchmark_dict.keys()))
        
        if not common_dates:
            return {
                "period": period,
                "portfolio_data": [],
                "benchmark_data": [],
                "message": "No overlapping data between portfolio and benchmark"
            }
        
        # 지수화를 위한 기준값 (첫 번째 날의 값)
        base_nav = nav_dict[common_dates[0]]
        base_benchmark = benchmark_dict[common_dates[0]]
        
        # 지수화된 데이터 생성
        for date_val in common_dates:
            nav_value = nav_dict[date_val]
            benchmark_value = benchmark_dict[date_val]
            
            # 100을 기준으로 지수화
            indexed_nav = (nav_value / base_nav) * 100
            indexed_benchmark = (benchmark_value / base_benchmark) * 100
            
            portfolio_data.append({
                "date": date_val.isoformat(),
                "value": indexed_nav
            })
            
            benchmark_data.append({
                "date": date_val.isoformat(),
                "value": indexed_benchmark,
                "name": benchmark_instrument.name
            })
        
        return {
            "period": period,
            "portfolio_name": portfolio.name,
            "benchmark_name": benchmark_instrument.name,
            "benchmark_symbol": benchmark_symbol,
            "portfolio_data": portfolio_data,
            "benchmark_data": benchmark_data,
            "start_date": common_dates[0].isoformat() if common_dates else None,
            "end_date": common_dates[-1].isoformat() if common_dates else None
        }
        
    except Exception as e:
        print(f"벤치마크 비교 차트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

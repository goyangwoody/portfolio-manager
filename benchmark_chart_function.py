def calculate_benchmark_vs_portfolio_chart(portfolio_id: int, chart_period: str, end_date: date, db) -> List[DailyReturnData]:
    """벤치마크와 포트폴리오 비교 차트 데이터 (지수화)"""
    try:
        # 포트폴리오 조회
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            return []

        # 차트 기간에 따른 시작일 계산
        start_date = get_chart_start_date(chart_period, end_date)
        
        # 포트폴리오 NAV 데이터 조회
        portfolio_navs = db.query(PortfolioNavDaily).filter(
            PortfolioNavDaily.portfolio_id == portfolio_id,
            PortfolioNavDaily.as_of_date >= start_date,
            PortfolioNavDaily.as_of_date <= end_date
        ).order_by(PortfolioNavDaily.as_of_date).all()
        
        if len(portfolio_navs) < 2:
            return []
        
        # 벤치마크 심볼 선택
        benchmark_symbol = get_benchmark_symbol_by_currency(portfolio.currency)
        
        # 벤치마크 인스트루먼트 조회
        benchmark_instrument = db.query(MarketInstrument).filter(
            MarketInstrument.symbol == benchmark_symbol,
            MarketInstrument.is_active == 'Yes'
        ).first()
        
        if not benchmark_instrument:
            return []
        
        # 벤치마크 가격 데이터 조회
        benchmark_data = db.query(MarketPriceDaily).filter(
            MarketPriceDaily.instrument_id == benchmark_instrument.id,
            MarketPriceDaily.date >= start_date,
            MarketPriceDaily.date <= end_date
        ).order_by(MarketPriceDaily.date).all()
        
        if len(benchmark_data) < 2:
            return []
        
        # 날짜별 데이터 매칭 및 지수화
        chart_data = []
        benchmark_dict = {bd.date: float(bd.close_price) for bd in benchmark_data}
        
        # 기준점 설정 (첫 번째 데이터)
        base_portfolio_nav = float(portfolio_navs[0].nav)
        base_benchmark_price = None
        
        # 첫 번째 날짜에 해당하는 벤치마크 가격 찾기
        for nav in portfolio_navs:
            if nav.as_of_date in benchmark_dict:
                base_benchmark_price = benchmark_dict[nav.as_of_date]
                break
        
        if not base_benchmark_price:
            return []
        
        for nav in portfolio_navs:
            nav_date = nav.as_of_date
            
            # 해당 날짜의 벤치마크 가격이 있는 경우만 처리
            if nav_date in benchmark_dict:
                # 포트폴리오 지수화 (100 기준)
                portfolio_index = (float(nav.nav) / base_portfolio_nav) * 100
                
                # 벤치마크 지수화 (100 기준)
                benchmark_index = (benchmark_dict[nav_date] / base_benchmark_price) * 100
                
                chart_data.append(DailyReturnData(
                    date=nav_date,
                    portfolio_return=portfolio_index,
                    benchmark_return=benchmark_index,
                    excess_return=portfolio_index - benchmark_index
                ))
        
        return chart_data
        
    except Exception as e:
        print(f"벤치마크 vs 포트폴리오 차트 계산 오류: {str(e)}")
        return []

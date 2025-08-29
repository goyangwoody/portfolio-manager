"""
개선된 시장 데이터 수집기
정규화된 DB 구조를 사용하여 데이터 수집
"""
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from pm.db.models import (
    MarketInstrument, MarketPriceDaily, RiskFreeRateDaily, MarketDataHelper,
    SessionLocal, engine, Base
)

class ImprovedMarketDataCollector:
    """개선된 시장 데이터 수집 클래스"""
    
    def __init__(self):
        # 테이블 생성 (없을 경우)
        Base.metadata.create_all(bind=engine)
        
        # 초기 마켓 인스트루먼트 데이터 생성
        db = SessionLocal()
        try:
            count = MarketDataHelper.initialize_instruments(db)
            print(f"📋 마켓 인스트루먼트 초기화 완료: {count} 개 상품")
        finally:
            db.close()

    def get_instrument_by_symbol(self, db, symbol: str) -> Optional[MarketInstrument]:
        """심볼로 마켓 인스트루먼트 조회"""
        return db.query(MarketInstrument).filter(
            MarketInstrument.symbol == symbol,
            MarketInstrument.is_active == 'Yes'
        ).first()

    def collect_price_data(self, start_date: str, end_date: str = None) -> None:
        """가격 데이터 수집 (주식 지수, 환율)"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        db = SessionLocal()
        try:
            # 가격 데이터가 있는 모든 인스트루먼트 조회
            instruments = db.query(MarketInstrument).filter(
                MarketInstrument.market_type.in_(['STOCK_INDEX', 'CURRENCY']),
                MarketInstrument.is_active == 'Yes'
            ).all()
            
            print(f"\n💰 가격 데이터 수집 중...")
            
            for instrument in instruments:
                try:
                    print(f"  - {instrument.symbol} ({instrument.name}) 수집 중...")
                    
                    # Yahoo Finance에서 데이터 가져오기
                    ticker = yf.Ticker(instrument.symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    
                    if hist.empty:
                        print(f"    경고: {instrument.symbol} 데이터가 없습니다.")
                        continue
                    
                    # 이전 종가 저장용 (일일 수익률 계산)
                    previous_close = None
                    new_records = 0
                    
                    # 데이터베이스에 저장
                    for date_idx, row in hist.iterrows():
                        # 기존 데이터 확인
                        existing = db.query(MarketPriceDaily).filter(
                            MarketPriceDaily.instrument_id == instrument.id,
                            MarketPriceDaily.date == date_idx.date()
                        ).first()
                        
                        if existing:
                            previous_close = row['Close']
                            continue  # 이미 존재하는 데이터는 스킵
                        
                        # 일일 수익률 계산
                        daily_return = None
                        if previous_close and previous_close != 0:
                            daily_return = ((row['Close'] - previous_close) / previous_close) * 100
                        
                        # 새 데이터 추가
                        price_data = MarketPriceDaily(
                            instrument_id=instrument.id,
                            date=date_idx.date(),
                            open_price=row.get('Open'),
                            high_price=row.get('High'),
                            low_price=row.get('Low'),
                            close_price=row['Close'],
                            volume=row.get('Volume') if pd.notna(row.get('Volume')) else None,
                            daily_return=daily_return
                        )
                        db.add(price_data)
                        new_records += 1
                        previous_close = row['Close']
                    
                    db.commit()
                    print(f"    완료: 전체 {len(hist)} 건 중 {new_records} 건의 새 데이터 저장")
                    
                except Exception as e:
                    print(f"    오류: {instrument.symbol} 데이터 수집 실패 - {str(e)}")
                    db.rollback()
                    continue
                    
        finally:
            db.close()

    def collect_risk_free_rate_data(self, start_date: str, end_date: str = None) -> None:
        """무위험 이자율 데이터 수집"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        db = SessionLocal()
        try:
            # 무위험 이자율 인스트루먼트 조회
            rate_instruments = db.query(MarketInstrument).filter(
                MarketInstrument.market_type == 'RATE',
                MarketInstrument.is_active == 'Yes'
            ).all()
            
            print(f"\n📊 무위험 이자율 데이터 수집 중...")
            
            for instrument in rate_instruments:
                try:
                    if instrument.symbol == 'KOR_BASE_RATE':
                        # 한국은행 기준금리는 수동 데이터 사용
                        self._collect_kr_base_rate(db, instrument, start_date, end_date)
                    else:
                        # 미국 이자율은 Yahoo Finance 사용
                        self._collect_us_treasury_rate(db, instrument, start_date, end_date)
                        
                except Exception as e:
                    print(f"    오류: {instrument.symbol} 데이터 수집 실패 - {str(e)}")
                    db.rollback()
                    continue
                    
        finally:
            db.close()

    def _collect_us_treasury_rate(self, db, instrument: MarketInstrument, start_date: str, end_date: str):
        """미국 국채 이자율 수집"""
        print(f"  - {instrument.symbol} ({instrument.name}) 수집 중...")
        
        # Yahoo Finance에서 데이터 가져오기
        ticker = yf.Ticker(instrument.symbol)
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty:
            print(f"    경고: {instrument.symbol} 데이터가 없습니다.")
            return
        
        new_records = 0
        
        # 데이터베이스에 저장
        for date_idx, row in hist.iterrows():
            # 기존 데이터 확인
            existing = db.query(RiskFreeRateDaily).filter(
                RiskFreeRateDaily.instrument_id == instrument.id,
                RiskFreeRateDaily.date == date_idx.date()
            ).first()
            
            if existing:
                continue  # 이미 존재하는 데이터는 스킵
            
            # 새 데이터 추가 (Yahoo Finance에서는 이자율이 Close 값으로 제공됨)
            rate_data = RiskFreeRateDaily(
                instrument_id=instrument.id,
                date=date_idx.date(),
                rate=row['Close'],  # 이자율 (%)
                rate_type='TREASURY_RATE'
            )
            db.add(rate_data)
            new_records += 1
        
        db.commit()
        print(f"    완료: 전체 {len(hist)} 건 중 {new_records} 건의 새 데이터 저장")

    def _collect_kr_base_rate(self, db, instrument: MarketInstrument, start_date: str, end_date: str):
        """한국은행 기준금리 수집 (수동 데이터)"""
        print(f"  - {instrument.symbol} ({instrument.name}) 수집 중...")
        
        # 예시: 2024년 한국은행 기준금리 (실제 데이터로 교체 필요)
        sample_rates = [
            {'date': '2000-01-01', 'rate': 5.00},  # 2000년 초기 금리
            {'date': '2008-10-01', 'rate': 2.00},  # 금융위기 시 인하
            {'date': '2020-03-01', 'rate': 0.75},  # 코로나19 대응
            {'date': '2022-01-01', 'rate': 1.25},  # 인플레이션 대응
            {'date': '2023-01-01', 'rate': 3.25},  # 추가 인상
            {'date': '2024-01-01', 'rate': 3.50},  # 2024년 금리
            {'date': '2024-11-28', 'rate': 3.00},  # 2024년 11월 기준금리 인하
        ]
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        new_records = 0
        
        for rate_info in sample_rates:
            rate_date = datetime.strptime(rate_info['date'], '%Y-%m-%d').date()
            
            # 날짜 범위 확인
            if rate_date < start_dt or rate_date > end_dt:
                continue
            
            # 기존 데이터 확인
            existing = db.query(RiskFreeRateDaily).filter(
                RiskFreeRateDaily.instrument_id == instrument.id,
                RiskFreeRateDaily.date == rate_date
            ).first()
            
            if existing:
                continue  # 이미 존재하는 데이터는 스킵
            
            # 새 데이터 추가
            rate_data = RiskFreeRateDaily(
                instrument_id=instrument.id,
                date=rate_date,
                rate=rate_info['rate'],
                rate_type='CENTRAL_BANK_RATE'
            )
            db.add(rate_data)
            new_records += 1
        
        db.commit()
        print(f"    완료: {new_records} 건의 새 데이터 저장")

    def collect_all_data(self, start_date: str, end_date: str = None) -> None:
        """모든 시장 데이터 수집"""
        print("=== 개선된 시장 데이터 수집 시작 ===")
        print(f"수집 기간: {start_date} ~ {end_date or '현재'}")
        
        # 가격 데이터 수집 (벤치마크 지수, 환율)
        self.collect_price_data(start_date, end_date)
        
        # 무위험 이자율 데이터 수집
        self.collect_risk_free_rate_data(start_date, end_date)
        
        print("\n=== 개선된 시장 데이터 수집 완료 ===")

    def get_latest_data_summary(self) -> None:
        """최신 데이터 요약 출력"""
        db = SessionLocal()
        try:
            print("\n=== 최신 시장 데이터 요약 ===")
            
            # 벤치마크 지수 최신 데이터
            print("\n📈 벤치마크 지수:")
            benchmarks = MarketDataHelper.get_benchmark_data(db)
            benchmark_latest = {}
            for benchmark in benchmarks:
                key = benchmark.symbol
                if key not in benchmark_latest or benchmark.date > benchmark_latest[key].date:
                    benchmark_latest[key] = benchmark
            
            for benchmark in benchmark_latest.values():
                return_str = f" ({benchmark.daily_return:+.2f}%)" if benchmark.daily_return else ""
                print(f"  {benchmark.name} ({benchmark.date}): {benchmark.close_price:,.2f} {benchmark.currency}{return_str}")
            
            # 환율 최신 데이터
            print("\n💱 환율:")
            exchanges = MarketDataHelper.get_exchange_rate_data(db)
            exchange_latest = {}
            for exchange in exchanges:
                key = exchange.currency_pair
                if key not in exchange_latest or exchange.date > exchange_latest[key].date:
                    exchange_latest[key] = exchange
            
            for exchange in exchange_latest.values():
                change_str = f" ({exchange.daily_return:+.2f}%)" if exchange.daily_return else ""
                print(f"  {exchange.currency_pair} ({exchange.date}): {exchange.close_rate:,.2f}{change_str}")
            
            # 무위험 이자율 최신 데이터
            print("\n📊 무위험 이자율:")
            rates = MarketDataHelper.get_risk_free_rate_data(db)
            rate_latest = {}
            for rate in rates:
                key = f"{rate.country}_{rate.symbol}"
                if key not in rate_latest or rate.date > rate_latest[key].date:
                    rate_latest[key] = rate
            
            for rate in rate_latest.values():
                print(f"  {rate.name} ({rate.date}): {rate.rate:.2f}%")
                
        finally:
            db.close()


def main():
    """메인 실행 함수"""
    collector = ImprovedMarketDataCollector()
    
    # 2000년 1월 1일부터 현재까지 모든 데이터 수집
    start_date = '2000-01-01'
    
    print(f"📊 장기간 시장 데이터 수집을 시작합니다.")
    print(f"📅 수집 기간: {start_date} ~ 현재")
    print(f"🏗️ 개선된 정규화 구조 사용")
    print(f"⏰ 대량 데이터이므로 시간이 오래 걸릴 수 있습니다...")
    
    try:
        # 데이터 수집
        collector.collect_all_data(start_date)
        
        # 최신 데이터 요약 출력
        collector.get_latest_data_summary()
        
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    main()

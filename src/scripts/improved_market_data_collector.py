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
import time

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pm.db.models import (
    MarketInstrument, MarketPriceDaily, RiskFreeRateDaily, MarketDataHelper,
    SessionLocal, engine, Base
)

class ProgressBar:
    """간단한 진행률 표시 클래스"""
    
    def __init__(self, total: int, prefix: str = "", length: int = 50):
        self.total = total
        self.prefix = prefix
        self.length = length
        self.current = 0
        self.start_time = time.time()
    
    def update(self, amount: int = 1, suffix: str = ""):
        """진행률 업데이트"""
        self.current += amount
        percent = (self.current / self.total) * 100
        filled_length = int(self.length * self.current // self.total)
        bar = '█' * filled_length + '░' * (self.length - filled_length)
        
        # 경과 시간 및 예상 남은 시간 계산
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f" ETA: {int(eta)}s" if eta > 1 else " ETA: <1s"
        else:
            eta_str = ""
        
        # 진행률 출력
        print(f'\r{self.prefix} |{bar}| {self.current}/{self.total} ({percent:.1f}%){eta_str} {suffix}', end='', flush=True)
        
        if self.current >= self.total:
            total_time = time.time() - self.start_time
            print(f'\n✅ 완료! 총 소요시간: {int(total_time)}초')


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
            
            print(f"\n💰 가격 데이터 수집 시작 ({len(instruments)}개 상품)")
            
            # 전체 인스트루먼트에 대한 진행률 바
            instrument_progress = ProgressBar(len(instruments), "📊 상품별 진행률")
            
            total_new_records = 0
            total_existing_records = 0
            
            for i, instrument in enumerate(instruments):
                try:
                    # Yahoo Finance에서 데이터 가져오기
                    ticker = yf.Ticker(instrument.symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    
                    if hist.empty:
                        instrument_progress.update(1, f"⚠️  {instrument.symbol}: 데이터 없음")
                        continue
                    
                    # 이전 종가 저장용 (일일 수익률 계산)
                    previous_close = None
                    new_records = 0
                    existing_records = 0
                    
                    # 날짜별 데이터 처리 진행률 바
                    date_progress = ProgressBar(len(hist), f"  📅 {instrument.symbol} 데이터 처리")
                    
                    # 데이터베이스에 저장
                    for date_idx, row in hist.iterrows():
                        # 기존 데이터 확인
                        existing = db.query(MarketPriceDaily).filter(
                            MarketPriceDaily.instrument_id == instrument.id,
                            MarketPriceDaily.date == date_idx.date()
                        ).first()
                        
                        if existing:
                            previous_close = row['Close']
                            existing_records += 1
                            date_progress.update(1, f"존재: {existing_records}")
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
                        
                        date_progress.update(1, f"신규: {new_records}")
                    
                    db.commit()
                    total_new_records += new_records
                    total_existing_records += existing_records
                    
                    instrument_progress.update(1, f"✅ {instrument.symbol}: 신규 {new_records}건, 기존 {existing_records}건")
                    
                    # API 제한을 피하기 위한 짧은 대기
                    time.sleep(0.1)
                    
                except Exception as e:
                    instrument_progress.update(1, f"❌ {instrument.symbol}: 오류")
                    print(f"\n    ⚠️  오류: {instrument.symbol} 데이터 수집 실패 - {str(e)}")
                    db.rollback()
                    continue
            
            print(f"\n🎉 가격 데이터 수집 완료!")
            print(f"   📈 총 신규 데이터: {total_new_records:,} 건")
            print(f"   📊 총 기존 데이터: {total_existing_records:,} 건")
                    
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
            
            print(f"\n📊 무위험 이자율 데이터 수집 시작 ({len(rate_instruments)}개 금리)")
            
            # 전체 금리 상품에 대한 진행률 바
            rate_progress = ProgressBar(len(rate_instruments), "💰 금리별 진행률")
            
            total_new_records = 0
            total_existing_records = 0
            
            for i, instrument in enumerate(rate_instruments):
                try:
                    print(f"\n🔄 {instrument.symbol} ({instrument.name}) 처리 중...")
                    
                    if instrument.symbol == 'KOR_BASE_RATE':
                        # 한국은행 기준금리는 수동 데이터 사용
                        new_count, existing_count = self._collect_kr_base_rate(db, instrument, start_date, end_date)
                    else:
                        # 미국 이자율은 Yahoo Finance 사용
                        new_count, existing_count = self._collect_us_treasury_rate(db, instrument, start_date, end_date)
                    
                    total_new_records += new_count
                    total_existing_records += existing_count
                    
                    rate_progress.update(1, f"✅ {instrument.symbol}: 신규 {new_count}건, 기존 {existing_count}건")
                        
                except Exception as e:
                    rate_progress.update(1, f"❌ {instrument.symbol}: 오류")
                    print(f"\n    ⚠️  오류: {instrument.symbol} 금리 데이터 수집 실패 - {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"\n🎉 무위험 이자율 데이터 수집 완료!")
            print(f"   💰 총 신규 데이터: {total_new_records:,} 건")
            print(f"   📊 총 기존 데이터: {total_existing_records:,} 건")
                    
        finally:
            db.close()

    def _collect_us_treasury_rate(self, db, instrument: MarketInstrument, start_date: str, end_date: str):
        """미국 국채 이자율 수집"""
        try:
            # Yahoo Finance에서 데이터 가져오기
            ticker = yf.Ticker(instrument.symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                print(f"⚠️  {instrument.symbol}: Yahoo Finance에서 데이터를 찾을 수 없습니다.")
                return 0, 0  # 신규 0건, 기존 0건
            
            new_records = 0
            existing_records = 0
            
            # 데이터베이스에 저장
            for date_idx, row in hist.iterrows():
                # 기존 데이터 확인
                existing = db.query(RiskFreeRateDaily).filter(
                    RiskFreeRateDaily.instrument_id == instrument.id,
                    RiskFreeRateDaily.date == date_idx.date()
                ).first()
                
                if existing:
                    existing_records += 1
                    continue  # 이미 존재하는 데이터는 스킵
                
                # 새 데이터 추가 (Yahoo Finance에서는 이자율이 Close 값으로 제공됨)
                rate_data = RiskFreeRateDaily(
                    instrument_id=instrument.id,
                    date=date_idx.date(),
                    rate=row['Close'],
                    rate_type='TREASURY_RATE'
                )
                db.add(rate_data)
                new_records += 1
            
            db.commit()
            return new_records, existing_records
            
        except Exception as e:
            print(f"❌ {instrument.symbol} 국채 이자율 수집 오류: {str(e)}")
            db.rollback()
            return 0, 0

    def _collect_kr_base_rate(self, db, instrument: MarketInstrument, start_date: str, end_date: str):
        """한국은행 기준금리 수집 (수동 데이터)"""
        try:
            # 예시: 2024년 한국은행 기준금리 (실제 데이터로 교체 필요)
            sample_rates = [
                {'date': '2020-01-01', 'rate': 1.25},  # 2020년 초기
                {'date': '2020-03-16', 'rate': 0.75},  # 코로나19 1차 인하
                {'date': '2020-05-28', 'rate': 0.50},  # 코로나19 2차 인하
                {'date': '2021-08-26', 'rate': 0.75},  # 정상화 시작
                {'date': '2021-11-25', 'rate': 1.00},  # 추가 인상
                {'date': '2022-01-14', 'rate': 1.25},  # 인플레이션 대응
                {'date': '2022-04-14', 'rate': 1.50},  # 추가 인상
                {'date': '2022-05-26', 'rate': 1.75},  # 추가 인상
                {'date': '2022-07-13', 'rate': 2.25},  # 추가 인상
                {'date': '2022-08-25', 'rate': 2.50},  # 추가 인상
                {'date': '2022-10-12', 'rate': 3.00},  # 추가 인상
                {'date': '2022-11-24', 'rate': 3.25},  # 추가 인상
                {'date': '2023-01-13', 'rate': 3.50},  # 최고점
                {'date': '2024-10-11', 'rate': 3.25},  # 인하 시작
                {'date': '2024-11-28', 'rate': 3.00},  # 추가 인하
            ]
            
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            new_records = 0
            existing_records = 0
            
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
                    existing_records += 1
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
            return new_records, existing_records
            
        except Exception as e:
            print(f"\n❌ 한국은행 기준금리 수집 오류: {str(e)}")
            db.rollback()
            return 0, 0

    def collect_all_data(self, start_date: str, end_date: str = None) -> None:
        """모든 시장 데이터 수집"""
        start_time = time.time()
        
        print("🚀 === 개선된 시장 데이터 수집 시작 ===")
        print(f"📅 수집 기간: {start_date} ~ {end_date or '현재'}")
        
        # 전체 진행률을 위한 큰 섹션들
        total_sections = 2
        section_progress = ProgressBar(total_sections, "🌐 전체 진행률")
        
        try:
            # 가격 데이터 수집 (벤치마크 지수, 환율)
            self.collect_price_data(start_date, end_date)
            section_progress.update(1, "💰 가격 데이터 완료")
            
            # 무위험 이자율 데이터 수집
            self.collect_risk_free_rate_data(start_date, end_date)
            section_progress.update(1, "📊 금리 데이터 완료")
            
            elapsed_time = time.time() - start_time
            print(f"\n🎉 === 개선된 시장 데이터 수집 완료 ===")
            print(f"⏱️  총 소요 시간: {elapsed_time:.1f}초")
            
        except Exception as e:
            print(f"\n❌ 데이터 수집 중 오류 발생: {str(e)}")
            raise

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

    # 2025년부터 현재까지 데이터 수집
    start_date = "2025-01-01"
    
    print(f"📊 시장 데이터 수집을 시작합니다.")
    print(f"📅 수집 기간: {start_date} ~ 현재")
    print(f"🏗️ 개선된 정규화 구조 사용")
    
    try:
        # 데이터 수집
        collector.collect_all_data(start_date)
        
        # 최신 데이터 요약 출력
        collector.get_latest_data_summary()
        
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

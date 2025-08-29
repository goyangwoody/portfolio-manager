#!/usr/bin/env python3
"""
Market Instruments 데이터 확인 스크립트
데이터베이스에 저장된 market instruments 데이터를 조회하고 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from src.pm.db.models import SessionLocal, MarketInstrument, MarketPriceDaily, RiskFreeRateDaily

def check_market_instruments():
    """Market Instruments 데이터 확인"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("🔍 MARKET INSTRUMENTS 데이터 확인")
        print("=" * 80)
        
        # 1. Market Instruments 테이블 전체 조회
        instruments = db.query(MarketInstrument).all()
        
        if not instruments:
            print("❌ Market Instruments 테이블에 데이터가 없습니다!")
            return
        
        print(f"✅ 총 {len(instruments)}개의 Market Instrument가 등록되어 있습니다.\n")
        
        # 2. 각 타입별로 분류해서 출력
        types = {}
        for inst in instruments:
            if inst.market_type not in types:
                types[inst.market_type] = []
            types[inst.market_type].append(inst)
        
        for market_type, inst_list in types.items():
            print(f"📊 {market_type} ({len(inst_list)}개)")
            print("-" * 60)
            for inst in inst_list:
                status = "🟢" if inst.is_active == "Yes" else "🔴"
                print(f"  {status} [{inst.symbol:12}] {inst.name} ({inst.country}, {inst.currency})")
            print()
        
        # 3. 가격 데이터 확인
        print("💰 가격 데이터 확인")
        print("-" * 60)
        
        # 각 인스트루먼트별로 가격 데이터 개수 확인
        for inst in instruments:
            price_count = db.query(MarketPriceDaily).filter(MarketPriceDaily.instrument_id == inst.id).count()
            print(f"  📈 {inst.symbol:12} | {inst.name:30} | 가격 데이터: {price_count:,}개")
        
        # 4. 최신 가격 데이터 확인
        print("\n📅 최신 가격 데이터 (최근 5건)")
        print("-" * 60)
        
        latest_prices = db.query(
            MarketInstrument.symbol,
            MarketInstrument.name,
            MarketPriceDaily.date,
            MarketPriceDaily.close_price
        ).join(MarketPriceDaily).order_by(
            MarketPriceDaily.date.desc()
        ).limit(5).all()
        
        for symbol, name, date, price in latest_prices:
            print(f"  📊 {symbol:12} | {name:25} | {date} | {price:,.4f}")
        
        # 5. 무위험 이자율 데이터 확인
        print("\n💸 무위험 이자율 데이터 확인")
        print("-" * 60)
        
        # RATE 타입 인스트루먼트만 필터링해서 확인
        rate_instruments = [inst for inst in instruments if inst.market_type == 'RATE']
        
        for inst in rate_instruments:
            rate_count = db.query(RiskFreeRateDaily).filter(RiskFreeRateDaily.instrument_id == inst.id).count()
            print(f"  💱 {inst.symbol:12} | {inst.name:30} | 이자율 데이터: {rate_count:,}개")
        
        # 6. 데이터 품질 체크
        print("\n🔍 데이터 품질 체크")
        print("-" * 60)
        
        # 중복 심볼 체크
        duplicate_symbols = db.execute(text("""
            SELECT symbol, COUNT(*) as count 
            FROM market_instruments 
            GROUP BY symbol 
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicate_symbols:
            print("  ⚠️  중복된 심볼이 발견되었습니다:")
            for symbol, count in duplicate_symbols:
                print(f"    - {symbol}: {count}개")
        else:
            print("  ✅ 중복된 심볼이 없습니다.")
        
        # 비활성 인스트루먼트 체크
        inactive_count = db.query(MarketInstrument).filter(MarketInstrument.is_active != 'Yes').count()
        if inactive_count > 0:
            print(f"  ⚠️  비활성 상태인 인스트루먼트: {inactive_count}개")
        else:
            print("  ✅ 모든 인스트루먼트가 활성 상태입니다.")
        
        print("\n" + "=" * 80)
        print("✅ Market Instruments 데이터 확인이 완료되었습니다!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def check_specific_instrument(symbol: str):
    """특정 인스트루먼트의 상세 정보 확인"""
    db = SessionLocal()
    
    try:
        print(f"🔍 '{symbol}' 인스트루먼트 상세 정보")
        print("=" * 60)
        
        instrument = db.query(MarketInstrument).filter(MarketInstrument.symbol == symbol).first()
        
        if not instrument:
            print(f"❌ '{symbol}' 인스트루먼트를 찾을 수 없습니다.")
            return
        
        print(f"📊 기본 정보:")
        print(f"  - ID: {instrument.id}")
        print(f"  - Symbol: {instrument.symbol}")
        print(f"  - Name: {instrument.name}")
        print(f"  - Market Type: {instrument.market_type}")
        print(f"  - Country: {instrument.country}")
        print(f"  - Currency: {instrument.currency}")
        print(f"  - Description: {instrument.description or 'N/A'}")
        print(f"  - Is Active: {instrument.is_active}")
        
        # 가격 데이터 확인
        price_count = db.query(MarketPriceDaily).filter(MarketPriceDaily.instrument_id == instrument.id).count()
        print(f"\n💰 가격 데이터: {price_count:,}건")
        
        if price_count > 0:
            # 최신 가격 데이터
            latest_price = db.query(MarketPriceDaily).filter(
                MarketPriceDaily.instrument_id == instrument.id
            ).order_by(MarketPriceDaily.date.desc()).first()
            
            print(f"  - 최신 데이터: {latest_price.date} | 종가: {latest_price.close_price:,.4f}")
            
            # 날짜 범위
            date_range = db.execute(text("""
                SELECT MIN(date) as min_date, MAX(date) as max_date 
                FROM market_price_daily 
                WHERE instrument_id = :instrument_id
            """), {"instrument_id": instrument.id}).fetchone()
            
            print(f"  - 데이터 범위: {date_range.min_date} ~ {date_range.max_date}")
        
        # 이자율 데이터 확인 (RATE 타입인 경우)
        if instrument.market_type == 'RATE':
            rate_count = db.query(RiskFreeRateDaily).filter(RiskFreeRateDaily.instrument_id == instrument.id).count()
            print(f"\n💸 이자율 데이터: {rate_count:,}건")
            
            if rate_count > 0:
                latest_rate = db.query(RiskFreeRateDaily).filter(
                    RiskFreeRateDaily.instrument_id == instrument.id
                ).order_by(RiskFreeRateDaily.date.desc()).first()
                
                print(f"  - 최신 이자율: {latest_rate.date} | {latest_rate.rate:.4f}% ({latest_rate.rate_type})")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 특정 심볼 조회
        symbol = sys.argv[1]
        check_specific_instrument(symbol)
    else:
        # 전체 조회
        check_market_instruments()

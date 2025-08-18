import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from pm.db.models import Asset, Price, engine, SessionLocal, Base

# 테이블 생성: 없으면 생성
Base.metadata.create_all(bind=engine)

def fetch_initial_and_update(tickers, default_start="2020-01-01"):
    """
    주어진 티커 리스트에 대해:
    - DB에 없는 티커는 'default_start'부터 전체 이력 데이터 초기 로드
    - 이미 존재하는 티커는 마지막 저장일 다음 날부터 오늘까지 업데이트
    """
    session = SessionLocal()
    try:
        for ticker in tickers:
            # Asset 조회 또는 생성
            asset = session.query(Asset).filter_by(ticker=ticker).first()
            if not asset:
                asset = Asset(ticker=ticker, name=ticker)
                session.add(asset)
                session.commit()
                start_date = default_start
                print(f"[INIT] {ticker}: 시작일 {start_date}로 초기 로드")
            else:
                last_price = (
                    session.query(Price)
                    .filter_by(asset_id=asset.id)
                    .order_by(Price.date.desc())
                    .first()
                )
                if last_price:
                    next_day = last_price.date + timedelta(days=1)
                    start_date = next_day.strftime("%Y-%m-%d")
                    print(f"[UPDATE] {ticker}: 마지막 저장일 {last_price.date} 이후로 업데이트")
                else:
                    start_date = default_start
                    print(f"[INIT] {ticker}: 데이터는 있으나 가격 기록이 없어 {start_date}부터 초기 로드")
            end_date = datetime.today().strftime("%Y-%m-%d")
            if start_date > end_date:
                print(f"{ticker}: 이미 최신 (마지막 날짜 {start_date})")
                continue

            # 데이터 다운로드
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            if data.empty:
                print(f"{ticker}: 새로운 데이터 없음 ({start_date}~{end_date})")
                continue

            # 가격 정보 저장
            for date, row in data.iterrows():
                close_data = row['Close']
                # 다중 티커 다운로드 시 Series 반환 처리
                if isinstance(close_data, pd.Series):
                    close_price = close_data.get(ticker)
                else:
                    close_price = close_data
                # 결측치 스킵
                if pd.isna(close_price):
                    continue
                price = Price(
                    asset_id=asset.id,
                    date=date.date(),
                    close=float(close_price)
                )
                session.merge(price)
            session.commit()
            print(f"{ticker}: {start_date}부터 {end_date}까지 저장 완료")
    finally:
        session.close()

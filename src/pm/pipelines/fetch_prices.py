import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from pm.db.models import Asset, Price, engine, SessionLocal, Base

# 테이블 생성: 없으면 생성
Base.metadata.create_all(bind=engine)

def fetch_initial_and_update(tickers, default_start="2020-01-01", force_start_date=None):
    """
    주어진 티커 리스트에 대해:
    - DB에 없는 티커는 'default_start'부터 전체 이력 데이터 초기 로드
    - 이미 존재하는 티커는 마지막 저장일 다음 날부터 오늘까지 업데이트
    - force_start_date가 지정되면 DB 조회 없이 해당 날짜부터 시작 (성능 최적화)
    """
    session = SessionLocal()
    try:
        # 성능 최적화: force_start_date가 지정되지 않은 경우에만 배치로 마지막 날짜 조회
        asset_last_dates = {}
        if not force_start_date:
            # 모든 관련 자산의 마지막 가격 날짜를 한 번에 조회
            from sqlalchemy import func
            last_dates_query = (
                session.query(
                    Asset.ticker,
                    func.max(Price.date).label('last_date')
                )
                .join(Price, Asset.id == Price.asset_id)
                .filter(Asset.ticker.in_(tickers))
                .group_by(Asset.ticker)
            ).all()
            
            asset_last_dates = {ticker: last_date for ticker, last_date in last_dates_query}
            print(f"[BATCH] {len(asset_last_dates)}개 자산의 마지막 날짜 조회 완료")

        total_tickers = len(tickers)
        for idx, ticker in enumerate(tickers, 1):
            # 진행상황 표시
            print(f"\n=== [{idx}/{total_tickers}] {ticker} 처리 중 (진행률: {idx/total_tickers*100:.1f}%) ===")
            
            # Asset 조회 또는 생성
            asset = session.query(Asset).filter_by(ticker=ticker).first()
            if not asset:
                asset = Asset(ticker=ticker, name=ticker)
                session.add(asset)
                session.commit()
                start_date = force_start_date or default_start
                print(f"[INIT] {ticker} (Asset ID: {asset.id}): 시작일 {start_date}로 초기 로드")
            else:
                print(f"[INFO] {ticker} (Asset ID: {asset.id}): 기존 자산 확인")
                if force_start_date:
                    start_date = force_start_date
                    print(f"[FORCE] {ticker}: 강제 시작일 {start_date} 사용")
                elif ticker in asset_last_dates:
                    last_date = asset_last_dates[ticker]
                    next_day = last_date + timedelta(days=1)
                    start_date = next_day.strftime("%Y-%m-%d")
                    print(f"[UPDATE] {ticker}: 마지막 저장일 {last_date} 이후로 업데이트")
                else:
                    start_date = default_start
                    print(f"[INIT] {ticker}: 데이터는 있으나 가격 기록이 없어 {start_date}부터 초기 로드")
                    
            end_date = datetime.today().strftime("%Y-%m-%d")
            if start_date > end_date:
                print(f"[SKIP] {ticker}: 이미 최신 (마지막 날짜 {start_date})")
                continue

            # 데이터 다운로드
            print(f"[DOWNLOAD] {ticker}: yfinance에서 데이터 다운로드 중... ({start_date} ~ {end_date})")
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            if data.empty:
                print(f"[NO_DATA] {ticker}: 새로운 데이터 없음 ({start_date}~{end_date})")
                continue

            # 가격 정보 저장
            print(f"[SAVING] {ticker}: 데이터베이스에 저장 중... ({len(data)}개 데이터)")
            saved_count = 0
            # 가격 정보 저장
            print(f"[SAVING] {ticker}: 데이터베이스에 저장 중... ({len(data)}개 데이터)")
            saved_count = 0
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
                saved_count += 1
            session.commit()
            print(f"[COMPLETE] {ticker} (Asset ID: {asset.id}): {saved_count}개 데이터 저장 완료 ({start_date}~{end_date})")
            print(f"[PROGRESS] 전체 진행률: {idx}/{total_tickers} 완료 ({idx/total_tickers*100:.1f}%)")
    finally:
        session.close()
        print(f"\n=== 전체 작업 완료 ===")
        print(f"총 {total_tickers}개 티커 처리 완료")



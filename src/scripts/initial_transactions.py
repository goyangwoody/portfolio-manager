"""
Batch insert transactions from an Excel file into the transactions table.
Each transaction spans two rows in the Excel:
  - First row: [ticker, datetime, type ("보통매수"/"보통매도"), quantity]
  - Second row: [ticker,            , asset name,                price]

Configure EXCEL_FILE and PORTFOLIO_NAME before running.
Usage:
    python src/db/batch_insert_transactions.py
"""
# src/db/batch_insert_transactions.py

import pandas as pd
import pandas_market_calendars as mcal
from pathlib import Path
from datetime import timedelta

from pm.db.models import SessionLocal, Portfolio, Asset
from pm.portfolio.insert_transaction import add_transaction

# === 설정 ===
EXCEL_FILE     = Path("transactions_0730_2027.xlsx")
PORTFOLIO_NAME = "Core"

# KRX 영업일 캘린더
krx = mcal.get_calendar("XKRX")


def load_transactions(path: Path):
    """
    두 줄씩 파싱:
      r1 = [ticker, settlement_date, type_kr, quantity,    tax ]
      r2 = [ticker,           _,    asset_name,   price,    fee ]
    """
    df = pd.read_excel(path, header=None, skiprows=2)
    n = len(df)
    if n % 2 != 0:
        raise ValueError(f"짝수 행이 아닙니다: {n}개 행")

    # 1) Settlement → Trade Date 계산용 캘린더
    raw_dates = pd.to_datetime(df[1].dropna()).dt.date
    start = raw_dates.min() - timedelta(days=10)
    end   = raw_dates.max()
    sched = krx.schedule(start_date=start, end_date=end)
    trade_days = sched.index.normalize()

    # 2) Asset name → ID 매핑
    session = SessionLocal()
    try:
        asset_map = {a.name: a.id for a in session.query(Asset).all()}
    finally:
        session.close()

    records = []
    for i in range(0, n, 2):
        r1, r2 = df.iloc[i], df.iloc[i+1]

        # --- (a) Settlement → Trade Date ---
        settle_raw = r1[1]
        if pd.isna(settle_raw):
            continue
        settle = pd.to_datetime(settle_raw).date()
        ts = pd.Timestamp(settle)
        if ts in trade_days:
            idx = trade_days.get_loc(ts)
        else:
            idx = trade_days.searchsorted(ts) - 1
        trade_idx = idx - 2
        if trade_idx < 0:
            raise ValueError(f"{settle} 이전 2영업일을 찾을 수 없습니다.")
        trans_dt = trade_days[trade_idx].date()

        # --- (b) 필드 파싱 ---
        qty        = float(r1[3])
        tax        = float(r1[4] or 0.0)       # r1의 5번째 칼럼
        asset_name = str(r2[2]).strip()
        asset_name = asset_name.replace("'","")
        price      = float(r2[3])
        fee        = float(r2[4] or 0.0)       # r2의 5번째 칼럼
        type_kr    = str(r1[2]).strip()

        # --- (c) 거래 유형 매핑 ---
        if '매수' in type_kr:
            type_ = 'BUY'
        elif '매도' in type_kr:
            type_ = 'SELL'
        elif '입금' in type_kr:
            type_ = 'DEPOSIT'
            trans_dt = trade_days[idx].date()  ## 배당 입금은 어차피 영업일에만 된다는 전제하에 2영업일을 빼기 전의 영업일 인덱스인 idx로 거래일 찾음
        else:
            type_ = type_kr.upper()

        # --- (d) asset_id lookup ---
        aid = asset_map.get(asset_name)
        if aid is None:
            print(f"[SKIP] 자산 미발견: {asset_name}")
            continue

        records.append({
            'asset_id' : aid,
            'trans_dt' : trans_dt,
            'type'     : type_,
            'quantity' : qty,
            'price'    : price,
            'fee'      : fee,
            'tax'      : tax,
            'type_kr'  : type_kr
        })

    return records


def main():
    txs = load_transactions(EXCEL_FILE)
    print(f"Loaded {len(txs)} transactions")
    txs.reverse()
    session = SessionLocal()
    try:
        portfolio = session.query(Portfolio)\
                           .filter_by(name=PORTFOLIO_NAME)\
                           .one_or_none()
        if portfolio is None:
            raise ValueError(f"포트폴리오 없음: {PORTFOLIO_NAME}")

        for tx in txs:
            add_transaction(
                portfolio_id=portfolio.id,
                asset_id    =tx['asset_id'],
                trans_date  =tx['trans_dt'],
                quantity    =tx['quantity'],
                price       =tx['price'],
                fee         =tx['fee'],
                tax         =tx['tax'],
                type_       =tx['type']
            )
            print(f"[INSERT] {tx['trans_dt']} {tx['type']} "
                  f"asset_id={tx['asset_id']} qty={tx['quantity']} "
                  f"price={tx['price']} fee={tx['fee']} tax={tx['tax']} type_kr={tx['type_kr']}")

        print("Batch insert complete.")
    finally:
        session.close()


if __name__ == '__main__':
    main()



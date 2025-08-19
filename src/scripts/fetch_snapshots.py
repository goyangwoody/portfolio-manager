# src/db/snapshot_all_history.py

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional, Sequence

from sqlalchemy import select, func
import pandas as pd
import pandas_market_calendars as mcal

from pm.db.models import SessionLocal, Portfolio, Transaction
from pm.portfolio.snapshot_positions import snapshot_portfolio_date

# 거래소 캘린더
krx = mcal.get_calendar("XKRX")
nyse = mcal.get_calendar("XNYS")


def _ensure_date(d: Optional[date | str]) -> Optional[date]:
    if d is None:
        return None
    if isinstance(d, date):
        return d
    # ISO 형식 'YYYY-MM-DD' 가정
    return date.fromisoformat(d)


def get_earliest_transaction_date() -> date:
    """transactions 테이블에서 가장 이른 거래일자를 가져옵니다."""
    session = SessionLocal()
    try:
        result = session.execute(select(func.min(Transaction.trans_date))).scalar_one()
        return result
    finally:
        session.close()


def get_all_portfolio_ids() -> list[int]:
    """모든 포트폴리오의 ID 리스트를 반환합니다."""
    session = SessionLocal()
    try:
        return session.execute(select(Portfolio.id)).scalars().all()
    finally:
        session.close()


def get_valid_portfolio_ids(requested_ids: Sequence[int]) -> list[int]:
    """
    DB에 존재하는 ID만 필터링해 반환합니다.
    """
    if not requested_ids:
        return []
    session = SessionLocal()
    try:
        rows = session.execute(
            select(Portfolio.id).where(Portfolio.id.in_(requested_ids))
        ).scalars().all()
        return list(rows)
    finally:
        session.close()


def get_trading_days_krx(start: date, end: date) -> list[date]:
    """start~end 사이의 KRX 영업일(date) 리스트"""
    schedule = krx.schedule(start_date=start, end_date=end)
    return [ts.date() for ts in schedule.index.normalize()]


def get_trading_days_nyse(start: date, end: date) -> list[date]:
    """start~end 사이의 NYSE 영업일(date) 리스트"""
    schedule = nyse.schedule(start_date=start, end_date=end)
    return [ts.date() for ts in schedule.index.normalize()]


def run_full_snapshot_krx(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    portfolio_ids: Optional[Sequence[int]] = None,
):
    """
    지정된 기간의 모든 KRX 영업일에 대해 snapshot_portfolio_date 실행.
    - start_date 미지정 시: transactions 최소 거래일 또는 오늘
    - end_date   미지정 시: 오늘
    - portfolio_ids 미지정 시: 전체 포트폴리오
    """
    today = date.today()
    end_date = _ensure_date(end_date) or today
    start_date = _ensure_date(start_date) or (get_earliest_transaction_date() or today)

    trading_days = get_trading_days_krx(start_date, end_date)
    if not trading_days:
        print("해당 기간에 영업일이 없습니다.")
        return

    if portfolio_ids is None:
        pids = get_all_portfolio_ids()
    else:
        pids = get_valid_portfolio_ids(list(dict.fromkeys(portfolio_ids)))  # 중복 제거
        missing = set(portfolio_ids) - set(pids)
        if missing:
            print(f"[WARN] 존재하지 않는 포트폴리오 ID 무시됨: {sorted(missing)}")
    if not pids:
        print("[INFO] 실행할 포트폴리오가 없습니다.")
        return

    for d in trading_days:
        for pid in pids:
            try:
                snapshot_portfolio_date(pid, d)
            except Exception as e:
                print(f"[ERROR] PID={pid}, DATE={d}: {e}")
        print(f"[SNAPSHOT] Completed for trading day: {d}")


def run_full_snapshot_nyse(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    portfolio_ids: Optional[Sequence[int]] = None,
):
    """
    지정된 기간의 모든 NYSE 영업일에 대해 snapshot_portfolio_date 실행.
    - start_date 미지정 시: transactions 최소 거래일 또는 오늘
    - end_date   미지정 시: 오늘
    - portfolio_ids 미지정 시: 전체 포트폴리오
    """
    today = date.today()
    end_date = _ensure_date(end_date) or today
    start_date = _ensure_date(start_date) or (get_earliest_transaction_date() or today)

    trading_days = get_trading_days_nyse(start_date, end_date)
    if not trading_days:
        print("해당 기간에 영업일이 없습니다.")
        return

    if portfolio_ids is None:
        pids = get_all_portfolio_ids()
    else:
        pids = get_valid_portfolio_ids(list(dict.fromkeys(portfolio_ids)))
        missing = set(portfolio_ids) - set(pids)
        if missing:
            print(f"[WARN] 존재하지 않는 포트폴리오 ID 무시됨: {sorted(missing)}")
    if not pids:
        print("[INFO] 실행할 포트폴리오가 없습니다.")
        return

    for d in trading_days:
        for pid in pids:
            try:
                snapshot_portfolio_date(pid, d)
            except Exception as e:
                print(f"[ERROR] PID={pid}, DATE={d}: {e}")
        print(f"[SNAPSHOT] Completed for trading day: {d}")


if __name__ == "__main__":

    run_full_snapshot_krx('2025-08-12', '2025-08-18', [1])

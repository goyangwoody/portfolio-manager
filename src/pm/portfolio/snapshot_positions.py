from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, Numeric
from pm.db.models import (
    SessionLocal,
    Portfolio,
    Transaction,
    Price,
    PortfolioPositionDaily,
    PortfolioNavDaily
)

def snapshot_portfolio_date(portfolio_id: int, as_of_date: date):
    session = SessionLocal()
    try:
        # ── 1) cash_balance 계산 (fee, tax 반영) ──
        p = session.get(Portfolio, portfolio_id)
        initial_cash = getattr(p, 'initial_cash', Decimal('0'))

        buy_out = session.execute(
            select(func.coalesce(func.sum(
                Transaction.quantity * Transaction.price
                + Transaction.fee
                + Transaction.tax
            ), Decimal('0')))
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type         == 'BUY',
                Transaction.trans_date   <= as_of_date
            )
        ).scalar()

        sell_in = session.execute(
            select(func.coalesce(func.sum(
                Transaction.quantity * Transaction.price
                - Transaction.fee
                - Transaction.tax
            ), Decimal('0')))
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type         == 'SELL',
                Transaction.trans_date   <= as_of_date
            )
        ).scalar()

        deposit_in = session.execute(
            select(func.coalesce(func.sum(
                Transaction.quantity * Transaction.price
                - Transaction.fee
                - Transaction.tax
            ), Decimal('0')))
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type == "DEPOSIT",
                Transaction.trans_date <= as_of_date
            )
        ).scalar()


        cash_balance = initial_cash - buy_out + sell_in + deposit_in

        # ── 2) 거래된 자산 리스트 ──
        asset_ids = session.execute(
            select(Transaction.asset_id)
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.trans_date   <= as_of_date
            )
            .distinct()
        ).scalars().all()

        # ── 3) 각 자산별 최신 종가 조회 ──
        price_map = {}
        for aid in asset_ids:
            px = session.execute(
                select(Price.close)
                .where(
                    Price.asset_id == aid,
                    Price.date     <= as_of_date
                )
                .order_by(Price.date.desc())
                .limit(1)
            ).scalar_one_or_none() or Decimal('0')
            price_map[aid] = px

        # ── 4) 자산별 상세 스냅샷 + total_market_value 집계 ──
        total_market_value = Decimal('0')

        for aid in asset_ids:
            # (a) 보유 수량 = BUY 합 − SELL 합
            buy_qty = session.execute(
                select(func.coalesce(func.sum(Transaction.quantity), Decimal('0')))
                .where(
                    Transaction.portfolio_id == portfolio_id,
                    Transaction.asset_id      == aid,
                    Transaction.type          == 'BUY',
                    Transaction.trans_date    <= as_of_date
                )
            ).scalar()
            sell_qty = session.execute(
                select(func.coalesce(func.sum(Transaction.quantity), Decimal('0')))
                .where(
                    Transaction.portfolio_id == portfolio_id,
                    Transaction.asset_id      == aid,
                    Transaction.type          == 'SELL',
                    Transaction.trans_date    <= as_of_date
                )
            ).scalar()
            total_qty = (buy_qty or Decimal('0')) - (sell_qty or Decimal('0'))

            # (b) 평균 매입단가 (BUY 만 반영)
            buy_qty2, buy_cost = session.execute(
                select(
                    func.coalesce(func.sum(Transaction.quantity), Decimal('0')),
                    func.coalesce(func.sum(Transaction.quantity * Transaction.price), Decimal('0'))
                ).where(
                    Transaction.portfolio_id == portfolio_id,
                    Transaction.asset_id      == aid,
                    Transaction.type          == 'BUY',
                    Transaction.trans_date    <= as_of_date
                )
            ).one()
            avg_price = (buy_cost / buy_qty2) if buy_qty2 else Decimal('0')

            # (c) market_value 계산
            mv = total_qty * price_map.get(aid, Decimal('0'))
            total_market_value += mv

            # (d) portfolio_positions_daily upsert
            existing = session.execute(
                select(PortfolioPositionDaily)
                .where(
                    PortfolioPositionDaily.portfolio_id == portfolio_id,
                    PortfolioPositionDaily.as_of_date   == as_of_date,
                    PortfolioPositionDaily.asset_id     == aid
                )
            ).scalar_one_or_none()

            if existing:
                existing.quantity     = total_qty
                existing.avg_price    = avg_price
                existing.market_value = mv
            else:
                session.add(PortfolioPositionDaily(
                    portfolio_id = portfolio_id,
                    as_of_date   = as_of_date,
                    asset_id     = aid,
                    quantity     = total_qty,
                    avg_price    = avg_price,
                    market_value = mv
                ))

        # ── 5) portfolio_nav_daily upsert ──
        total_nav = cash_balance + total_market_value

        existing_nav = session.execute(
            select(PortfolioNavDaily)
            .where(
                PortfolioNavDaily.portfolio_id == portfolio_id,
                PortfolioNavDaily.as_of_date   == as_of_date
            )
        ).scalar_one_or_none()

        if existing_nav:
            existing_nav.cash_balance       = cash_balance
            existing_nav.total_market_value = total_market_value
            existing_nav.nav                = total_nav
        else:
            session.add(PortfolioNavDaily(
                portfolio_id        = portfolio_id,
                as_of_date          = as_of_date,
                cash_balance        = cash_balance,
                total_market_value  = total_market_value,
                nav                 = total_nav
            ))

        session.commit()
    finally:
        session.close()

"""
Print all transactions in the database in a tabular format.
Usage:
    python src/db/print_transactions.py
"""
from datetime import datetime
from sqlalchemy import select
from pm.db.models import SessionLocal, Transaction, Portfolio, Asset


def print_transactions():
    session = SessionLocal()
    try:
        # Query all transactions, joined with portfolio and asset for names
        stmt = (
            select(
                Transaction.id,
                Transaction.trans_date,
                Portfolio.name.label('portfolio'),
                Asset.ticker.label('asset'),
                Transaction.type,
                Transaction.quantity,
                Transaction.price,
                Transaction.fee,
                Transaction.tax
            )
            .join(Portfolio, Transaction.portfolio_id == Portfolio.id)
            .join(Asset, Transaction.asset_id == Asset.id)
            .order_by(Transaction.trans_date, Transaction.id)
        )
        rows = session.execute(stmt).all()

        # Print header
        header = ["ID", "Date", "Portfolio", "Asset", "Type", "Qty", "Price", "Fee", "Tax"]
        print("\t".join(header))
        print("-" * 80)
        # Print each row
        for row in rows:
            print(
                f"{row.id}\t{row.trans_date.strftime('%Y-%m-%d')}\t"
                f"{row.portfolio}\t{row.asset}\t{row.type}\t"
                f"{row.quantity}\t{row.price}\t{row.fee}\t{row.tax}"
            )
    finally:
        session.close()

if __name__ == '__main__':
    print_transactions()

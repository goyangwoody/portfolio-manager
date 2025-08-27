#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, argparse
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from pm.db.models import engine  # engine 은 SQLAlchemy 2.0 Engine

# DEFAULT_TABLES = [
#     "assets",
#     "prices",
#     "portfolios",
#     "transactions",
#     "portfolio_positions_daily"
# ]

DEFAULT_TABLES = [
    "transactions"
]
def export_table(table_name, out_dir, chunksize=None, gzip=False):
    path = os.path.join(out_dir, f"{table_name}.csv" + (".gz" if gzip else ""))
    if chunksize and table_name == "prices":
        first = True
        with engine.connect() as conn:
            for chunk in pd.read_sql(text(f"SELECT * FROM {table_name}"), conn, chunksize=chunksize):
                chunk.to_csv(path, index=False, mode='w' if first else 'a',
                             header=first, compression='gzip' if gzip else None)
                first = False
    else:
        with engine.connect() as conn:
            df = pd.read_sql(text(f"SELECT * FROM {table_name}"), conn)
        df.to_csv(path, index=False, compression='gzip' if gzip else None)
    print(f"[OK] {table_name} -> {path}")

def export_price_pivot(out_dir, gzip=False):
    fname = os.path.join(out_dir, "prices_pivot.csv" + (".gz" if gzip else ""))
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT a.ticker, p.date, p.close
            FROM prices p
            JOIN assets a ON a.id = p.asset_id
            ORDER BY p.date
        """), conn)
    pivot = df.pivot(index="date", columns="ticker", values="close")
    pivot.to_csv(fname, compression='gzip' if gzip else None)
    print(f"[OK] prices_pivot -> {fname}")

def write_manifest(tables, out_dir):
    manifest = {}
    with engine.connect() as conn:
        for t in tables:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
            manifest[t] = {"row_count": int(cnt)}
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("[OK] manifest.json")

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", nargs="*", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--prices-chunksize", type=int, default=100000)
    ap.add_argument("--pivot", action="store_true")
    ap.add_argument("--gzip", action="store_true")
    return ap.parse_args()

def main():
    args = parse_args()
    tables = args.tables or DEFAULT_TABLES
    out_dir = args.out_dir or f"db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(out_dir, exist_ok=True)

    for t in tables:
        export_table(t, out_dir, chunksize=args.prices_chunksize, gzip=args.gzip)

    if args.pivot:
        export_price_pivot(out_dir, gzip=args.gzip)

    write_manifest(tables, out_dir)
    print("완료:", out_dir)

if __name__ == "__main__":
    main()

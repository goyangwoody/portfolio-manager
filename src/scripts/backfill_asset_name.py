"""
Backfill Asset.name from a hard-coded CSV mapping file.
The CSV file should have two columns:
  - ticker: Asset.ticker match
  - name:  full asset name to populate
Usage:
    python src/db/backfill_asset_names.py
"""
import pandas as pd
from pathlib import Path
from sqlalchemy import select
from pm.db.models import SessionLocal, Asset

# Hard-coded mapping file path
MAPPING_FILE = Path("tickers_names.csv")

def load_mapping(path: Path) -> list[tuple[str, str]]:
    """
    Load mapping of ticker to asset name from CSV.
    Expects columns 'ticker' and 'name'; if absent, uses first two columns.
    """
    if not path.exists():
        raise FileNotFoundError(f"Mapping file not found: {path}")
    df = pd.read_csv(path)

    cols = [c.lower() for c in df.columns]
    if 'ticker' in cols and 'name' in cols:
        tcol = df.columns[cols.index('ticker')]
        ncol = df.columns[cols.index('name')]
    else:
        tcol, ncol = df.columns[0], df.columns[1]

    mapping = []
    for _, row in df.iterrows():
        ticker = str(row[tcol]).strip()
        name   = str(row[ncol]).strip()
        if ticker:
            mapping.append((ticker, name))
    return mapping


def backfill_asset_names(mapping: list[tuple[str, str]]):
    """
    Update Asset.name based on mapping list
    """
    session = SessionLocal()
    updated, missing = 0, []
    try:
        for ticker, name in mapping:
            stmt = select(Asset).where(Asset.ticker == ticker)
            asset = session.execute(stmt).scalar_one_or_none()
            if asset is None:
                missing.append(ticker)
                print(f"[MISSING] {ticker}: no such asset record")
                continue
            if asset.name == name:
                print(f"[SKIP]    {ticker}: name already '{name}'")
                continue
            asset.name = name
            session.add(asset)
            updated += 1
            print(f"[UPDATE]  {ticker}: set name -> {name}")
        session.commit()
        print(f"\nDone. {updated} updated, {len(missing)} missing.")
        if missing:
            print("Missing tickers:", ", ".join(missing))
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main():
    mapping = load_mapping(MAPPING_FILE)
    backfill_asset_names(mapping)


if __name__ == '__main__':
    main()

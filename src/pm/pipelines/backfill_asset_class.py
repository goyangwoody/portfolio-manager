"""
Backfill asset_class field in assets table using:
- data/tickers.csv  (column: ticker  또는 첫 열에 티커)
- data/groups.xlsx  (column: group   또는 첫 열에 자산군 코드)

순서는 두 파일이 1:1로 대응한다고 가정.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import select
from pm.db.models import SessionLocal, Asset, ASSET_CLASS_ENUM

# === 경로 설정 ===
TICKER_CSV_PATH = Path("data/tickers.csv")
GROUPS_XLSX_PATH = Path("data/groups.xlsx")    # 엑셀 확장자(.xlsx) 가정

def load_mapping() -> list[tuple[str, str]]:
    """
    tickers.csv와 groups.xlsx를 읽어 (ticker, group) 리스트 반환.
    groups.xlsx 이 없거나 행 수가 다르면 예외 발생.
    """
    if not TICKER_CSV_PATH.exists():
        raise FileNotFoundError(f"tickers.csv not found: {TICKER_CSV_PATH}")
    if not GROUPS_XLSX_PATH.exists():
        raise FileNotFoundError(f"groups.xlsx not found: {GROUPS_XLSX_PATH}")

    tickers_df = pd.read_csv(TICKER_CSV_PATH)
    groups_df = pd.read_excel(GROUPS_XLSX_PATH)

    # 컬럼명 유연 처리: 'ticker' / 'group' 없으면 첫 컬럼 사용
    if 'ticker' not in tickers_df.columns:
        tickers_df.columns = ['ticker'] + list(tickers_df.columns[1:])
    if 'group' not in groups_df.columns:
        groups_df.columns = ['group'] + list(groups_df.columns[1:])

    if len(tickers_df) != len(groups_df):
        raise ValueError(
            f"Row count mismatch: tickers({len(tickers_df)}) vs groups({len(groups_df)})"
        )

    mapping: list[tuple[str, str]] = []
    for i in range(len(tickers_df)):
        t = str(tickers_df.iloc[i]['ticker']).strip()
        g = str(groups_df.iloc[i]['group']).strip()
        mapping.append((t, g))
    return mapping

def validate_group(group: str) -> None:
    if group not in ASSET_CLASS_ENUM:
        raise ValueError(f"Invalid asset_class '{group}' not in allowed ENUM list")

def backfill():
    mapping = load_mapping()
    session = SessionLocal()

    updated = 0
    missing = []
    skipped = []
    invalid = []

    try:
        for ticker, group in mapping:
            # ENUM 검증
            try:
                validate_group(group)
            except ValueError as e:
                print(f"[INVALID ENUM] {ticker}: {e}")
                invalid.append(ticker)
                continue

            # 자산 조회
            stmt = select(Asset).where(Asset.ticker == ticker)
            asset = session.execute(stmt).scalar_one_or_none()

            if asset is None:
                print(f"[MISSING] {ticker}: assets 테이블에 없음")
                missing.append(ticker)
                continue

            # 동일 값이면 스킵
            if asset.asset_class == group:
                print(f"[SKIP SAME] {ticker}: already '{group}'")
                skipped.append(ticker)
                continue

            # 업데이트
            asset.asset_class = group
            session.add(asset)
            updated += 1
            print(f"[UPDATE] {ticker}: set asset_class -> {group}")

        session.commit()
        print("\n=== Backfill Summary ===")
        print(f" Updated : {updated}")
        print(f" Missing : {len(missing)} {'(' + ', '.join(missing) + ')' if missing else ''}")
        print(f" Skipped : {len(skipped)}")
        print(f" Invalid : {len(invalid)} {'(' + ', '.join(invalid) + ')' if invalid else ''}")
    except Exception as e:
        session.rollback()
        print("❌ 백필 작업 중 오류 발생, 롤백했습니다.")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    backfill()

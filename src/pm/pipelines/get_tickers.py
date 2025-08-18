#!/usr/bin/env python3
# get_tickers.py

import argparse
from pathlib import Path
from typing import Union, Optional
import pandas as pd

def convert_excel_to_csv(
    excel_path: Union[str, Path],
    csv_path: Union[str, Path] = "krw_ticker.csv",
    ticker_col: Optional[str] = None,
) -> None:
    """
    엑셀 파일에 들어 있는 AXXXXXX 형태의 한국 주식 티커를
    XXXXXX.KS 형태로 변환해 CSV로 저장합니다.
    """
    df = pd.read_excel(excel_path, dtype=str)

    # 티커 열 결정
    col = ticker_col if (ticker_col and ticker_col in df.columns) else df.columns[0]

    # 'AXXXXX' → 'XXXXXX.KS'
    tickers = (
        df[col]
        .str.strip()
        .str.upper()
        .str.replace(r"^A", "", regex=True)
        .str.cat([".KS"] * len(df), na_rep="")
    )

    tickers.to_frame(name="Ticker") \
           .to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"✔ {csv_path} 저장 완료 ({len(tickers)}개)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert AXXXXXX-form tickers in an Excel file to XXXXXX.KS CSV"
    )
    parser.add_argument(
        "excel_path",
        help="원본 엑셀(.xlsx) 파일 경로"
    )
    parser.add_argument(
        "-c", "--column",
        help="티커가 들어 있는 열 이름 (기본: 첫 번째 열)",
        default=None
    )
    parser.add_argument(
        "-o", "--output",
        help="결과 CSV 파일 이름 (기본: krw_ticker.csv)",
        default="krw_ticker.csv"
    )
    args = parser.parse_args()

    convert_excel_to_csv(
        excel_path=args.excel_path,
        csv_path=args.output,
        ticker_col=args.column
    )

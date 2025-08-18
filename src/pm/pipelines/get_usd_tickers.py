#!/usr/bin/env python3
# get_equity_tickers.py

import argparse
import pandas as pd

def extract_base_ticker(
    excel_path: str,
    output_csv: str = "usd_tickers.csv",
    ticker_col: str = None,
) -> None:
    """
    Excel 파일에서 'XXX UW Equity' 또는 'XXX UN Equity' 형태의 문자열을 읽어
    'XXX' 부분만 추출하고 CSV로 저장합니다.

    Parameters
    ----------
    excel_path : str
        원본 엑셀(.xlsx) 파일 경로
    output_csv : str, default "krw_ticker.csv"
        결과 CSV 파일 이름
    ticker_col : str, default None
        티커 열 이름. None이면 첫 번째 열을 사용.
    """
    # 1) 엑셀 읽기 (모든 값을 문자열로)
    df = pd.read_excel(excel_path, dtype=str)

    # 2) 티커가 담긴 열 찾기
    if ticker_col and ticker_col in df.columns:
        col = ticker_col
    else:
        col = df.columns[0]

    # 3) 'XXX UW Equity' → 'XXX'
    base = (
        df[col]
        .str.strip()
        .str.split(r"\s+", n=1, expand=True)[0]
    )

    # 4) CSV 저장
    base.to_frame(name="Ticker").to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✔ {output_csv} 저장 완료 ({len(base)}개)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract base tickers (XXX) from 'XXX UW/UN Equity' and save to CSV"
    )
    parser.add_argument(
        "excel_path",
        help="원본 엑셀(.xlsx) 파일 경로"
    )
    parser.add_argument(
        "-c", "--column",
        help="티커가 있는 열 이름 (기본: 첫 번째 열)",
        default=None
    )
    parser.add_argument(
        "-o", "--output",
        help="결과 CSV 파일명 (기본: krw_ticker.csv)",
        default="usd_tickers.csv"
    )
    args = parser.parse_args()

    extract_base_ticker(
        excel_path=args.excel_path,
        output_csv=args.output,
        ticker_col=args.column
    )

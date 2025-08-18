# src/data_fetch/load_tickers.py
import pandas as pd
import sys

def load_tickers(csv_path: str) -> list[str]:
    """
    CSV 파일에서 'ticker' 컬럼을 읽어 리스트로 반환합니다.
    """
    df = pd.read_csv(csv_path)
    if 'ticker' not in df.columns:
        raise ValueError("CSV에 'ticker' 컬럼이 없습니다.")
    return df['ticker'].dropna().astype(str).tolist()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python load_tickers.py <path_to_csv>")
        sys.exit(1)
    csv_path = sys.argv[1]
    try:
        tickers = load_tickers(csv_path)
        print(tickers)
    except Exception as e:
        print(f"Error loading tickers: {e}")
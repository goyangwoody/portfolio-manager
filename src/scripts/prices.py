from datetime import datetime
from pm.db.models import Base, engine
from pm.pipelines.fetch_prices import fetch_initial_and_update
from pm.pipelines.load_tickers import load_tickers

# 테이블 생성
Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    # 티커 리스트 로드
    tickers = load_tickers('src/pm/data/seed/tickers.csv')
    # 과거 전체 이력 데이터 로드
    fetch_initial_and_update(tickers, default_start='2000-01-01')
    print('Initial fetch completed.')

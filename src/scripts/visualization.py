from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import FuncFormatter
from sqlalchemy import select, and_
from pm.db.models import SessionLocal, Asset, Price
import matplotlib.pyplot as plt

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False


def plot_asset_price(asset_name: str, start_date: str, end_date: str):
    session = SessionLocal()
    try:
        # 자산 ID 조회
        asset = session.execute(
            select(Asset).where(Asset.name == asset_name)
        ).scalar_one_or_none()

        if asset is None:
            print(f"[오류] 자산 '{asset_name}'을(를) 찾을 수 없습니다.")
            return

        asset_id = asset.id

        # 가격 정보 조회
        prices = session.execute(
            select(Price.date, Price.close)
            .where(
                and_(
                    Price.asset_id == asset_id,
                    Price.date >= datetime.strptime(start_date, "%Y-%m-%d").date(),
                    Price.date <= datetime.strptime(end_date, "%Y-%m-%d").date()
                )
            )
            .order_by(Price.date)
        ).all()

        if not prices:
            print(f"[경고] 선택한 기간 동안 '{asset_name}'의 가격 데이터가 없습니다.")
            return

        # 날짜, 종가 분리
        dates, closes = zip(*prices)

        # 그래프 그리기
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(dates, closes, marker='o', linestyle='-', color='blue', linewidth=2, markersize=5, label='Close Price')

        # 최신 종가에 주석 추가
        ax.annotate(
            f"{closes[-1]:,.2f}",
            xy=(dates[-1], closes[-1]),
            xytext=(10, 0),
            textcoords='offset points',
            ha='left',
            va='center',
            fontsize=10,
            color='darkred',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='red', alpha=0.5)
        )

        # X축 날짜 포맷: 'MM-DD'만 표시
        ax.xaxis.set_major_formatter(DateFormatter("%m-%d"))
        fig.autofmt_xdate()

        # Y축 가격 포맷: 통화 형식
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}원"))

        # 제목, 축 레이블, 그리드 등
        ax.set_title(f"{asset_name} Close Price: {start_date} ~ {end_date}", fontsize=14)
        ax.set_xlabel("Date")
        ax.set_ylabel("Close Price (KRW)")
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()
        plt.tight_layout()
        plt.show()

    finally:
        session.close()


# 사용 예시
plot_asset_price("TIGER 코스피", "2025-07-01", "2025-07-30")

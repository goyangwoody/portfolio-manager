import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from sqlalchemy import select, func
from pm.db.models import (
    SessionLocal,
    Portfolio,
    PortfolioPositionDaily,
    PortfolioNavDaily,
    Price,
    Asset
)



plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False


def period_attribution(
    portfolio_name: str,
    start_date: date,
    end_date: date,
    top_n: int = 5
):
    """
    Simple allocation-based attribution over ANY date range.
    
    Args:
      portfolio_name: name of your portfolio in the DB.
      start_date, end_date: period to analyze (inclusive).
      top_n: how many top/bottom assets to show.
    
    Returns:
      asset_df, class_df  (same as before) and plots the charts.
    """
    session = SessionLocal()
    try:
        # 1) find portfolio id
        pf = session.execute(
            select(Portfolio).where(Portfolio.name == portfolio_name)
        ).scalar_one()
        pid = pf.id

        # 2) locate the nearest snapshots on or after start_date,
        #    and on or before end_date
        start_snap = session.execute(
            select(func.min(PortfolioPositionDaily.as_of_date))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date   >= start_date
            )
        ).scalar_one()
        end_snap = session.execute(
            select(func.max(PortfolioPositionDaily.as_of_date))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date   <= end_date
            )
        ).scalar_one()

        # 3) load positions and NAV at start_snap
        rows = session.execute(
            select(
                PortfolioPositionDaily.asset_id,
                PortfolioPositionDaily.market_value
            ).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date   == start_snap
            )
        ).all()
        df_start = pd.DataFrame(rows, columns=['asset_id','market_value'])
        nav_start = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == pid,
                PortfolioNavDaily.as_of_date   == start_snap
            )
        ).scalar_one()

        df_start['weight'] = df_start['market_value'] / nav_start

        # 4) load prices at start_snap and end_snap
        ps = session.execute(
            select(Price.asset_id, Price.close)
            .where(Price.date == start_snap)
        ).all()
        pe = session.execute(
            select(Price.asset_id, Price.close)
            .where(Price.date == end_snap)
        ).all()
        df_price = (
            pd.DataFrame(ps, columns=['asset_id','price_start'])
            .merge(pd.DataFrame(pe, columns=['asset_id','price_end']), on='asset_id')
        )
        df_price['return'] = df_price['price_end']/df_price['price_start'] - 1

        # 5) merge, compute contributions
        df = df_start.merge(df_price, on='asset_id')
        df = df.merge(
            pd.DataFrame(
                session.execute(select(Asset.id, Asset.name, Asset.asset_class)).all(),
                columns=['asset_id','name','asset_class']
            ), on='asset_id'
        )
        df['contrib_pct'] = df['weight'] * df['return']
        df['contrib_abs'] = df['contrib_pct'] * nav_start

    finally:
        session.close()

    # 6) sort & split top/bottom
    df = df.sort_values('contrib_pct', ascending=False).reset_index(drop=True)
    top = df.head(top_n)
    bot = df.tail(top_n).iloc[::-1]

    # 7) group by asset_class
    class_df = df.groupby('asset_class')[['contrib_pct','contrib_abs']]\
                 .sum().reset_index().sort_values('contrib_pct', ascending=False)

    # # 8) plotting
    # fig, axes = plt.subplots(3,1,figsize=(10,12))
    # axes[0].bar(top['name'], top['contrib_pct']*100)
    # axes[0].set_title  (f"Top {top_n} Contributors\n{start_snap} → {end_snap}")
    # axes[0].set_ylabel("Contribution (%)")
    # axes[1].bar(bot['name'], bot['contrib_pct']*100)
    # axes[1].set_title  (f"Top {top_n} Detractors\n{start_snap} → {end_snap}")
    # axes[1].set_ylabel("Contribution (%)")
    # axes[2].bar(class_df['asset_class'], class_df['contrib_pct']*100)
    # axes[2].set_title  (f"Asset Class Contributions\n{start_snap} → {end_snap}")
    # axes[2].set_ylabel("Contribution (%)")
    # axes[2].tick_params(axis='x', rotation=45)
    # plt.tight_layout()
    # plt.show()

    return df, class_df


# 1) Attribution 계산
asset_df, class_df = period_attribution(
    portfolio_name="Core",
    start_date=date(2025, 7,7),
    end_date=date(2025, 8,8),
    top_n=5
)

def annotate_bars(ax, bars, fmt="{:.2f}%"):
    """각 바 위에 텍스트 라벨을 붙입니다."""
    for bar in bars:
        h = bar.get_height()
        ax.annotate(
            fmt.format(h),
            xy=(bar.get_x() + bar.get_width()/2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom"
        )


# 차트 그리기 직전: object → float 캐스팅
asset_df['contrib_pct'] = asset_df['contrib_pct'].astype(float)
class_df['contrib_pct'] = class_df['contrib_pct'].astype(float)

# 2) Top 5 기여자 차트
top = asset_df.nlargest(5, 'contrib_pct')
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(top['name'], top['contrib_pct']*100)
ax.set_title("Top 5 Asset Contributors (Jul 2025)")
ax.set_ylabel("Contribution (%)")
annotate_bars(ax, bars)
plt.xticks(rotation=15)
plt.tight_layout()
plt.show()

# 3) Top 5 저해자 차트
bot = asset_df.nsmallest(5, 'contrib_pct')
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(bot['name'], bot['contrib_pct']*100)
ax.set_title("Top 5 Asset Detractors (Jul 2025)")
ax.set_ylabel("Contribution (%)")
annotate_bars(ax, bars)
plt.xticks(rotation=15)
plt.tight_layout()
plt.show()

# 4) 자산군별 기여도 차트
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(class_df['asset_class'], class_df['contrib_pct']*100)
ax.set_title("Asset Class Contributions (Jul 2025)")
ax.set_ylabel("Contribution (%)")
annotate_bars(ax, bars)
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

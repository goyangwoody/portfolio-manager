from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import select, func
from decimal import Decimal
from pm.db.models import SessionLocal, Portfolio, PortfolioPositionDaily, Price, Asset, AssetClassReturnDaily

def plot_asset_class_daily_returns_twr(
    portfolio_name: str,
    start_date: date,
    end_date: date,
    annotate_last: bool = True,
    use_decimal: bool = True,
):
    session = SessionLocal()
    try:
        pid = session.execute(
            select(Portfolio.id).where(Portfolio.name == portfolio_name)
        ).scalar_one()

        # start_date 직전 스냅샷(실제 저장일)
        prev_weight_date = session.execute(
            select(func.max(PortfolioPositionDaily.as_of_date)).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date < start_date
            )
        ).scalar()
        start_pos_date = prev_weight_date or start_date

        # (1) 포지션
        pos_rows = session.execute(
            select(
                PortfolioPositionDaily.as_of_date,
                PortfolioPositionDaily.asset_id,
                PortfolioPositionDaily.market_value
            ).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date >= start_pos_date,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).all()
        # Convert to DataFrame and ensure Decimal type for market_value
        pos = pd.DataFrame(pos_rows, columns=['date','asset_id','mv'])
        if use_decimal:
            pos['mv'] = pos['mv'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else x)
        if pos.empty:
            print("해당 기간에 포지션 데이터가 없습니다.")
            return pd.DataFrame()

        # (2) 가격
        asset_ids = pos['asset_id'].unique().tolist()
        pr_rows = session.execute(
            select(Price.asset_id, Price.date, Price.close).where(
                Price.asset_id.in_(asset_ids),
                Price.date >= start_pos_date,
                Price.date <= end_date
            )
        ).all()
        prices = pd.DataFrame(pr_rows, columns=['asset_id','date','close'])
        if use_decimal:
            prices['close'] = prices['close'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else x)
        if prices.empty:
            print("해당 기간에 가격 데이터가 없습니다.")
            return pd.DataFrame()

        prices.sort_values(['asset_id','date'], inplace=True)
        
        if use_decimal:
            # Decimal을 사용한 수익률 계산
            def calc_return(group):
                returns = []
                prev_close = None
                for close in group:
                    if prev_close is None:
                        returns.append(None)
                    else:
                        ret = (close / prev_close) - Decimal('1')
                        returns.append(ret)
                    prev_close = close
                return returns
            
            prices['ret'] = prices.groupby('asset_id')['close'].transform(calc_return)
        else:
            prices['ret'] = prices.groupby('asset_id')['close'].pct_change()

        # (3) 자산군 메타
        meta_rows = session.execute(select(Asset.id, Asset.asset_class)).all()
        cls_map = pd.Series({aid: cls for aid, cls in meta_rows}, name='asset_class')
    finally:
        session.close()

   

    # 전일 MV 비중 (스냅샷 기준)
    mv_wide = pos.pivot(index='date', columns='asset_id', values='mv').sort_index()
    prev_mv = mv_wide.shift(1)
    
    if use_decimal:
        # Decimal을 사용한 비중 계산
        def calc_weights(row):
            total = sum(x for x in row if pd.notna(x))
            if total == 0:
                return [Decimal('0') if pd.notna(x) else x for x in row]
            return [Decimal(str(x/total)) if pd.notna(x) else x for x in row]
        
        w = prev_mv.apply(calc_weights, axis=1, result_type='expand')
        w.columns = prev_mv.columns
    else:
        w = prev_mv.div(prev_mv.sum(axis=1), axis=0)

    # 분석 구간 슬라이스 (Timestamp 기준)
    w = w.loc[(w.index >= start_date)]
    w = w.loc[:end_date]

    # 일일 수익률 매트릭스
    ret_wide = prices.pivot(index='date', columns='asset_id', values='ret').sort_index()
    # 날짜/자산 정합: 가중치 기준으로 재색인
    ret_wide = ret_wide.reindex_like(w)

    # === 기여 매트릭스: 전일비중 × 당일수익률 ===
    if use_decimal:
        # Decimal을 사용한 기여도 계산
        contrib = pd.DataFrame(index=w.index, columns=w.columns)
        for date_idx in w.index:
            for col in w.columns:
                weight = w.loc[date_idx, col]
                ret = ret_wide.loc[date_idx, col]
                if pd.notna(weight) and pd.notna(ret):
                    contrib.loc[date_idx, col] = weight * ret
                else:
                    contrib.loc[date_idx, col] = None
    else:
        contrib = w * ret_wide

    # === 자산군 집계 ===
    valid_cols = [c for c in contrib.columns if c in cls_map.index]
    contrib = contrib[valid_cols]
    by_class = []
    for cls, ids in cls_map.groupby(cls_map).groups.items():
        ids = [i for i in ids if i in contrib.columns]
        if not ids:
            continue
        if use_decimal:
            class_sum = contrib[ids].apply(lambda row: sum(x for x in row if pd.notna(x)), axis=1)
        else:
            class_sum = contrib[ids].sum(axis=1)
        by_class.append(class_sum.rename(cls))

    if not by_class:
        print("자산군 집계 결과가 비었습니다.")
        return pd.DataFrame()

    class_ret = pd.concat(by_class, axis=1)
    if not use_decimal:
        class_ret = class_ret.astype(float)

    # === 플롯 === 
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in class_ret.columns:
        ax.plot(class_ret.index, class_ret[col]*100, marker='o', label=str(col))
    ax.set_title(f"Asset Class Daily Returns (TWR)\n{start_date} ~ {end_date}")
    ax.set_ylabel("Daily Return (%)")
    ax.set_xlabel("Date")
    ax.legend(loc="best")
    plt.xticks(rotation=30)
    plt.tight_layout()

    if annotate_last and not class_ret.empty:
        last_x = class_ret.index[-1]
        for col in class_ret.columns:
            y = class_ret.loc[last_x, col]*100
            if pd.notna(y):
                ax.annotate(f"{y:.2f}%",
                            xy=(last_x, y),
                            xytext=(5, 0),
                            textcoords="offset points",
                            va="center", ha="left")

    plt.show()
    return class_ret

def compute_and_save_asset_class_returns(
    portfolio_name: str,
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    자산군별 일일 수익률을 계산하여 DB에 저장
    - 전일 자산군 가중치 × 당일 개별자산 수익률 → 자산군 합산
    - 신규편입(전일 MV=0)은 그날 기여 0 → 다음날부터 반영
    
    Returns:
        DataFrame with columns: [date, asset_class, daily_return]
    """
    session = SessionLocal()
    try:
        # Get portfolio id
        pid = session.execute(
            select(Portfolio.id).where(Portfolio.name == portfolio_name)
        ).scalar_one()

        # Calculate returns using Decimal arithmetic
        class_ret = plot_asset_class_daily_returns_twr(
            portfolio_name=portfolio_name,
            start_date=start_date,
            end_date=end_date,
            annotate_last=False,  # Don't show plot
            use_decimal=True      # Use Decimal for calculations
        )

        if class_ret.empty:
            print("수익률 계산 결과가 비었습니다.")
            return pd.DataFrame()

        # Convert to records for DB
        records = []
        for dt in class_ret.index:
            for asset_class in class_ret.columns:
                daily_return = class_ret.loc[dt, asset_class]
                if pd.notna(daily_return):
                    records.append(
                        AssetClassReturnDaily(
                            portfolio_id=pid,
                            date=dt,
                            asset_class=asset_class,
                            daily_return=Decimal(str(daily_return))  # Convert float to Decimal
                        )
                    )

        # Upsert to DB
        session.query(AssetClassReturnDaily).filter(
            AssetClassReturnDaily.portfolio_id == pid,
            AssetClassReturnDaily.date.between(start_date, end_date)
        ).delete()

        session.bulk_save_objects(records)
        session.commit()

        print(f"{len(records)}개의 자산군 일일 수익률 기록이 저장되었습니다.")
        return class_ret

    finally:
        session.close()

if __name__ == '__main__':
    # Example usage
    compute_and_save_asset_class_returns(
        portfolio_name="Core",
        start_date=date(2025, 7, 10),
        end_date=date(2025, 7, 31)
    )
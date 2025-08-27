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

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def analyze_specific_asset(portfolio_name: str, asset_name: str, start_date: date, end_date: date):
    """특정 자산의 상세 분석"""
    session = SessionLocal()
    try:
        # 1) 포트폴리오 ID 조회
        pid = session.execute(
            select(Portfolio.id).where(Portfolio.name == portfolio_name)
        ).scalar()
        
        if not pid:
            print(f"Portfolio '{portfolio_name}' not found")
            return
            
        # 2) 자산 ID 조회
        asset = session.execute(
            select(Asset.id, Asset.name, Asset.asset_class)
            .where(Asset.name == asset_name)
        ).first()
        
        if not asset:
            print(f"Asset '{asset_name}' not found")
            return
            
        aid = asset.id
        print(f"\n=== {asset_name} ({asset.asset_class}) 상세 분석 ===")
        
        # 3) 분석 기간 내 스냅샷 조회 (해당 자산 기준)
        start_snap = session.execute(
            select(func.max(PortfolioPositionDaily.as_of_date))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.asset_id == aid,
                PortfolioPositionDaily.as_of_date <= start_date
            )
        ).scalar()
        
        end_snap = session.execute(
            select(func.max(PortfolioPositionDaily.as_of_date))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.asset_id == aid,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).scalar()
        
        # 만약 해당 자산에 대한 포지션 데이터가 없다면 전체 포트폴리오 기준으로 찾기
        if not start_snap:
            start_snap = session.execute(
                select(func.max(PortfolioPositionDaily.as_of_date))
                .where(
                    PortfolioPositionDaily.portfolio_id == pid,
                    PortfolioPositionDaily.as_of_date <= start_date
                )
            ).scalar()
            
        if not end_snap:
            end_snap = session.execute(
                select(func.max(PortfolioPositionDaily.as_of_date))
                .where(
                    PortfolioPositionDaily.portfolio_id == pid,
                    PortfolioPositionDaily.as_of_date <= end_date
                )
            ).scalar()
        
        if not start_snap or not end_snap:
            print(f"No position data in range {start_date} ~ {end_date}")
            return
            
        print(f"분석 기간: {start_snap} → {end_snap}")
        
        # 해당 자산이 분석 기간 내에 포지션이 있었는지 확인
        asset_exists = session.execute(
            select(func.count(PortfolioPositionDaily.asset_id))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.asset_id == aid,
                PortfolioPositionDaily.as_of_date >= start_snap,
                PortfolioPositionDaily.as_of_date <= end_snap
            )
        ).scalar()
        
        if asset_exists == 0:
            print(f"자산 '{asset_name}'은 분석 기간 {start_snap} ~ {end_snap} 동안 포지션이 없었습니다.")
            return
        
        # 4) 포트폴리오 NAV 조회
        start_nav = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == pid,
                PortfolioNavDaily.as_of_date == start_snap
            )
        ).scalar()
        
        end_nav = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == pid,
                PortfolioNavDaily.as_of_date == end_snap
            )
        ).scalar()
        
        print(f"포트폴리오 NAV: {float(start_nav):,.0f} → {float(end_nav):,.0f}")
        portfolio_return = (float(end_nav) - float(start_nav)) / float(start_nav)
        print(f"포트폴리오 수익률: {portfolio_return:.4f} ({portfolio_return*100:.2f}%)")
        
        # 5) 자산 포지션 조회
        start_pos = session.execute(
            select(
                PortfolioPositionDaily.market_value,
                PortfolioPositionDaily.quantity,
                PortfolioPositionDaily.avg_price
            ).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.asset_id == aid,
                PortfolioPositionDaily.as_of_date == start_snap
            )
        ).first()
        
        end_pos = session.execute(
            select(
                PortfolioPositionDaily.market_value,
                PortfolioPositionDaily.quantity,
                PortfolioPositionDaily.avg_price
            ).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.asset_id == aid,
                PortfolioPositionDaily.as_of_date == end_snap
            )
        ).first()
        
        start_mv = float(start_pos.market_value) if start_pos else 0
        end_mv = float(end_pos.market_value) if end_pos else 0
        
        print(f"포지션 조회 결과:")
        print(f"  시작 포지션 존재: {'예' if start_pos else '아니오'}")
        print(f"  종료 포지션 존재: {'예' if end_pos else '아니오'}")
        
        if not start_pos and not end_pos:
            print(f"자산 '{asset_name}'의 포지션 데이터를 찾을 수 없습니다.")
            print("분석 기간 내 포지션 히스토리를 확인해보겠습니다...")
            
            # 분석 기간 내 모든 포지션 확인
            all_positions = session.execute(
                select(
                    PortfolioPositionDaily.as_of_date,
                    PortfolioPositionDaily.market_value
                ).where(
                    PortfolioPositionDaily.portfolio_id == pid,
                    PortfolioPositionDaily.asset_id == aid,
                    PortfolioPositionDaily.as_of_date >= start_snap,
                    PortfolioPositionDaily.as_of_date <= end_snap
                ).order_by(PortfolioPositionDaily.as_of_date)
            ).all()
            
            if all_positions:
                print(f"분석 기간 내 {len(all_positions)}개 포지션 발견:")
                for pos in all_positions[:5]:  # 처음 5개만 표시
                    print(f"  {pos.as_of_date}: {float(pos.market_value):,.0f}")
                if len(all_positions) > 5:
                    print(f"  ... 및 {len(all_positions)-5}개 추가")
            else:
                print("분석 기간 내 포지션이 전혀 없습니다.")
            return
        
        print(f"\n--- 포지션 정보 ---")
        print(f"시작 시장가치: {start_mv:,.0f}")
        print(f"종료 시장가치: {end_mv:,.0f}")
        
        if start_pos:
            print(f"시작 수량: {float(start_pos.quantity):,.2f}")
            print(f"시작 평균가: {float(start_pos.avg_price):,.2f}")
        
        if end_pos:
            print(f"종료 수량: {float(end_pos.quantity):,.2f}")
            print(f"종료 평균가: {float(end_pos.avg_price):,.2f}")
            print(f"종료 현재가: {end_mv/float(end_pos.quantity):,.2f}" if float(end_pos.quantity) > 0 else "")
        
        # 6) 수익률 계산
        print(f"\n--- 수익률 분석 ---")
        
        if start_mv > 0:
            # 기존 포지션
            asset_return = (end_mv - start_mv) / start_mv
            weight = start_mv / float(start_nav)
            print(f"자산 수익률: {asset_return:.4f} ({asset_return*100:.2f}%)")
            print(f"포트폴리오 가중치: {weight:.4f} ({weight*100:.2f}%)")
            
        elif end_mv > 0:
            # 신규 편입 - 편입 시점 찾기
            print("신규 편입 자산입니다.")
            
            # 편입 시점 찾기
            entry_date = session.execute(
                select(func.min(PortfolioPositionDaily.as_of_date))
                .where(
                    PortfolioPositionDaily.portfolio_id == pid,
                    PortfolioPositionDaily.asset_id == aid,
                    PortfolioPositionDaily.as_of_date >= start_snap,
                    PortfolioPositionDaily.as_of_date <= end_snap,
                    PortfolioPositionDaily.market_value > 0
                )
            ).scalar()
            
            if entry_date:
                print(f"편입 날짜: {entry_date}")
                
                # 편입 시점 포지션 조회
                entry_pos = session.execute(
                    select(
                        PortfolioPositionDaily.market_value,
                        PortfolioPositionDaily.quantity,
                        PortfolioPositionDaily.avg_price
                    ).where(
                        PortfolioPositionDaily.portfolio_id == pid,
                        PortfolioPositionDaily.asset_id == aid,
                        PortfolioPositionDaily.as_of_date == entry_date
                    )
                ).first()
                
                if entry_pos:
                    entry_mv = float(entry_pos.market_value)
                    entry_qty = float(entry_pos.quantity)
                    entry_price = float(entry_pos.avg_price)
                    current_price = end_mv / float(end_pos.quantity) if end_pos and float(end_pos.quantity) > 0 else 0
                    
                    print(f"편입 시장가치: {entry_mv:,.0f}")
                    print(f"편입 가격: {entry_price:,.2f}")
                    print(f"현재 가격: {current_price:,.2f}")
                    
                    if entry_price > 0:
                        asset_return = (current_price - entry_price) / entry_price
                        print(f"편입 후 수익률: {asset_return:.4f} ({asset_return*100:.2f}%)")
                    else:
                        print("편입 가격 정보 없음")
                        asset_return = 0
                else:
                    print("편입 시점 포지션 정보 없음")
                    asset_return = 0
            else:
                print("편입 시점을 찾을 수 없음")
                asset_return = 0
                
            weight = 0
        else:
            # 매도된 포지션 - 매도 시점 찾기
            print("분석 기간 중 매도된 자산입니다.")
            
            # 매도 시점 찾기 (마지막으로 포지션이 있었던 날)
            exit_date = session.execute(
                select(func.max(PortfolioPositionDaily.as_of_date))
                .where(
                    PortfolioPositionDaily.portfolio_id == pid,
                    PortfolioPositionDaily.asset_id == aid,
                    PortfolioPositionDaily.as_of_date >= start_snap,
                    PortfolioPositionDaily.as_of_date <= end_snap,
                    PortfolioPositionDaily.market_value > 0
                )
            ).scalar()
            
            if exit_date and start_pos:
                print(f"매도 날짜: {exit_date}")
                
                # 매도 시점 포지션 조회
                exit_pos = session.execute(
                    select(
                        PortfolioPositionDaily.market_value,
                        PortfolioPositionDaily.quantity,
                        PortfolioPositionDaily.avg_price
                    ).where(
                        PortfolioPositionDaily.portfolio_id == pid,
                        PortfolioPositionDaily.asset_id == aid,
                        PortfolioPositionDaily.as_of_date == exit_date
                    )
                ).first()
                
                if exit_pos:
                    exit_mv = float(exit_pos.market_value)
                    exit_qty = float(exit_pos.quantity)
                    exit_price = exit_mv / exit_qty if exit_qty > 0 else 0
                    start_price = float(start_pos.avg_price)
                    
                    print(f"시작 가격: {start_price:,.2f}")
                    print(f"매도 가격: {exit_price:,.2f}")
                    print(f"매도 시장가치: {exit_mv:,.0f}")
                    
                    if start_price > 0:
                        asset_return = (exit_price - start_price) / start_price
                        print(f"매도까지 수익률: {asset_return:.4f} ({asset_return*100:.2f}%)")
                    else:
                        print("시작 가격 정보 없음")
                        asset_return = 0
                        
                    # 기여도는 실제로는 (매도가치 - 시작가치) / 시작NAV 이지만
                    # 분석 기간 끝에는 포지션이 없으므로 -(시작가치) / 시작NAV
                    print(f"매도로 인한 기여도: {(exit_mv - start_mv) / float(start_nav):.4f}")
                else:
                    print("매도 시점 포지션 정보 없음")
                    asset_return = 0
            else:
                print("매도 시점을 찾을 수 없거나 시작 포지션 없음")
                asset_return = 0
                
            weight = start_mv / float(start_nav) if start_mv > 0 else 0
        
        # 7) 기여도 계산
        contrib_pct = (end_mv - start_mv) / float(start_nav)
        print(f"\n--- 기여도 분석 ---")
        print(f"절대 기여도: {contrib_pct:.4f} ({contrib_pct*100:.2f}%)")
        print(f"상대 기여도: {contrib_pct/portfolio_return*100:.1f}% (전체 수익률 대비)")
        
        # 8) 전체 기간 포지션 히스토리 조회 (옵션)
        print(f"\n--- 기간 내 포지션 변화 ---")
        positions_history = session.execute(
            select(
                PortfolioPositionDaily.as_of_date,
                PortfolioPositionDaily.market_value,
                PortfolioPositionDaily.quantity,
                PortfolioPositionDaily.avg_price
            ).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.asset_id == aid,
                PortfolioPositionDaily.as_of_date >= start_snap,
                PortfolioPositionDaily.as_of_date <= end_snap,
                PortfolioPositionDaily.market_value > 0
            ).order_by(PortfolioPositionDaily.as_of_date)
        ).all()
        
        print(f"총 {len(positions_history)}개 거래일 포지션 보유")
        if len(positions_history) <= 10:
            # 10개 이하면 모두 출력
            for pos in positions_history:
                current_price = float(pos.market_value) / float(pos.quantity) if float(pos.quantity) > 0 else 0
                print(f"  {pos.as_of_date}: MV={float(pos.market_value):,.0f}, "
                      f"Qty={float(pos.quantity):,.1f}, AvgPrice={float(pos.avg_price):,.2f}, "
                      f"CurrentPrice={current_price:,.2f}")
        else:
            # 처음 3개, 마지막 3개만 출력
            for pos in positions_history[:3]:
                current_price = float(pos.market_value) / float(pos.quantity) if float(pos.quantity) > 0 else 0
                print(f"  {pos.as_of_date}: MV={float(pos.market_value):,.0f}, "
                      f"Qty={float(pos.quantity):,.1f}, AvgPrice={float(pos.avg_price):,.2f}, "
                      f"CurrentPrice={current_price:,.2f}")
            print("  ...")
            for pos in positions_history[-3:]:
                current_price = float(pos.market_value) / float(pos.quantity) if float(pos.quantity) > 0 else 0
                print(f"  {pos.as_of_date}: MV={float(pos.market_value):,.0f}, "
                      f"Qty={float(pos.quantity):,.1f}, AvgPrice={float(pos.avg_price):,.2f}, "
                      f"CurrentPrice={current_price:,.2f}")
        
    except Exception as e:
        print(f"분석 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def annotate_bars(ax, bars, fmt='{:.2f}%'):
    """차트 바 위에 값 표시"""
    for bar in bars:
        h = bar.get_height()
        ax.annotate(
            fmt.format(h),
            xy=(bar.get_x() + bar.get_width()/2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9
        )


def debug_contribution_calculation(portfolio_name: str, start_date: date, end_date: date, asset_name: str = None):
    """특정 자산의 기여도 계산 과정을 자세히 분석
    
    Args:
        portfolio_name: 포트폴리오 이름
        start_date: 시작일  
        end_date: 종료일
        asset_name: 분석할 자산 이름 (None이면 전체)
    """
    session = SessionLocal()
    try:
        # 포트폴리오 ID 조회
        pf = session.execute(
            select(Portfolio).where(Portfolio.name == portfolio_name)
        ).scalar_one()
        pid = pf.id
        
        # 기간 내 스냅샷 조회
        start_snap = session.execute(
            select(func.min(PortfolioPositionDaily.as_of_date))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date >= start_date
            )
        ).scalar()
        
        end_snap = session.execute(
            select(func.max(PortfolioPositionDaily.as_of_date))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).scalar()
        
        print(f"=== 기여도 계산 디버그: {portfolio_name} ===")
        print(f"분석 기간: {start_snap} ~ {end_snap}")
        
        # NAV 조회
        start_nav = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == pid,
                PortfolioNavDaily.as_of_date == start_snap
            )
        ).scalar()
        
        end_nav = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == pid,
                PortfolioNavDaily.as_of_date == end_snap
            )
        ).scalar()
        
        total_return = (float(end_nav) - float(start_nav)) / float(start_nav)
        print(f"포트폴리오 전체 수익률: {total_return:.4f} ({total_return*100:.2f}%)")
        print(f"NAV: {start_nav:,.0f} → {end_nav:,.0f}")
        
        # 자산별 포지션 조회
        if asset_name:
            # 특정 자산만
            asset_id = session.execute(
                select(Asset.id).where(Asset.name == asset_name)
            ).scalar()
            
            if not asset_id:
                print(f"자산 '{asset_name}'을 찾을 수 없습니다.")
                return
                
            asset_filter = Asset.id == asset_id
        else:
            # 전체 자산
            asset_filter = Asset.id.isnot(None)
        
        # 시작 포지션
        start_positions = session.execute(
            select(
                PortfolioPositionDaily.asset_id,
                PortfolioPositionDaily.market_value,
                PortfolioPositionDaily.quantity,
                PortfolioPositionDaily.avg_price,
                Asset.name
            )
            .join(Asset, PortfolioPositionDaily.asset_id == Asset.id)
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date == start_snap,
                asset_filter
            )
        ).all()
        
        # 종료 포지션
        end_positions = session.execute(
            select(
                PortfolioPositionDaily.asset_id,
                PortfolioPositionDaily.market_value,
                PortfolioPositionDaily.quantity,
                PortfolioPositionDaily.avg_price,
                Asset.name
            )
            .join(Asset, PortfolioPositionDaily.asset_id == Asset.id)
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date == end_snap,
                asset_filter
            )
        ).all()
        
        # 분석
        start_dict = {pos.asset_id: pos for pos in start_positions}
        end_dict = {pos.asset_id: pos for pos in end_positions}
        all_assets = set(start_dict.keys()) | set(end_dict.keys())
        
        print(f"\n=== 자산별 상세 분석 ===")
        total_contrib = 0
        
        for aid in all_assets:
            start_pos = start_dict.get(aid)
            end_pos = end_dict.get(aid)
            
            asset_name = (start_pos.name if start_pos else end_pos.name) if (start_pos or end_pos) else f"Asset_{aid}"
            
            start_mv = float(start_pos.market_value) if start_pos else 0
            end_mv = float(end_pos.market_value) if end_pos else 0
            
            # 방법 1: 정확한 수익률 계산
            if start_mv > 0:
                # 기존 포지션: 일반적인 수익률 계산
                asset_return = (end_mv - start_mv) / start_mv
                weight = start_mv / float(start_nav)
                contrib1 = weight * asset_return
                return_str = f"{asset_return:.4f}"
            elif end_mv > 0:
                # 신규 편입: 편입 시점을 찾아서 정확한 수익률 계산
                entry_date = session.execute(
                    select(func.min(PortfolioPositionDaily.as_of_date))
                    .where(
                        PortfolioPositionDaily.portfolio_id == pid,
                        PortfolioPositionDaily.asset_id == aid,
                        PortfolioPositionDaily.as_of_date >= start_snap,
                        PortfolioPositionDaily.as_of_date <= end_snap,
                        PortfolioPositionDaily.market_value > 0
                    )
                ).scalar()
                
                if entry_date and end_pos and end_pos.quantity:
                    # 편입 시점의 평균가격 조회
                    entry_pos = session.execute(
                        select(PortfolioPositionDaily.avg_price)
                        .where(
                            PortfolioPositionDaily.portfolio_id == pid,
                            PortfolioPositionDaily.asset_id == aid,
                            PortfolioPositionDaily.as_of_date == entry_date
                        )
                    ).scalar()
                    
                    if entry_pos:
                        current_price = end_mv / float(end_pos.quantity)
                        asset_return = (current_price - float(entry_pos)) / float(entry_pos)
                        return_str = f"{asset_return:.4f}(NEW@{entry_date})"
                    else:
                        asset_return = 0
                        return_str = f"NEW@{entry_date}(No Price)"
                else:
                    asset_return = 0
                    return_str = "NEW(No Entry Date)"
                weight = 0
                contrib1 = end_mv / float(start_nav)
            else:
                # 매도된 포지션 - 매도 시점의 가격으로 수익률 계산
                if start_mv > 0:
                    # 매도 시점 찾기
                    exit_date = session.execute(
                        select(func.max(PortfolioPositionDaily.as_of_date))
                        .where(
                            PortfolioPositionDaily.portfolio_id == pid,
                            PortfolioPositionDaily.asset_id == aid,
                            PortfolioPositionDaily.as_of_date >= start_snap,
                            PortfolioPositionDaily.as_of_date <= end_snap,
                            PortfolioPositionDaily.market_value > 0
                        )
                    ).scalar()
                    
                    if exit_date and start_pos:
                        # 매도 시점 포지션 조회
                        exit_pos = session.execute(
                            select(
                                PortfolioPositionDaily.market_value,
                                PortfolioPositionDaily.quantity
                            ).where(
                                PortfolioPositionDaily.portfolio_id == pid,
                                PortfolioPositionDaily.asset_id == aid,
                                PortfolioPositionDaily.as_of_date == exit_date
                            )
                        ).first()
                        
                        if exit_pos and start_pos.avg_price:
                            exit_mv_calc = float(exit_pos.market_value)
                            exit_qty = float(exit_pos.quantity)
                            exit_price = exit_mv_calc / exit_qty if exit_qty > 0 else 0
                            start_price = float(start_pos.avg_price)
                            
                            asset_return = (exit_price - start_price) / start_price if start_price > 0 else 0
                            return_str = f"{asset_return:.4f}(SOLD@{exit_date})"
                            contrib1 = (exit_mv_calc - start_mv) / float(start_nav)
                        else:
                            asset_return = 0
                            return_str = f"SOLD@{exit_date}(No Price)"
                            contrib1 = -start_mv / float(start_nav)
                    else:
                        asset_return = 0
                        return_str = "SOLD(No Exit Date)"
                        contrib1 = -start_mv / float(start_nav)
                else:
                    asset_return = 0
                    return_str = "SOLD"
                    contrib1 = 0
                    
                weight = start_mv / float(start_nav) if start_mv > 0 else 0
            
            # 방법 2: 정확한 기여도 (NAV 변화 기준)
            contrib2 = (end_mv - start_mv) / float(start_nav)
            
            total_contrib += contrib2
            
            if abs(contrib2) > 0.001:  # 0.1% 이상만 출력
                print(f"\n{asset_name}:")
                print(f"  시작 MV: {start_mv:,.0f} ({weight:.4f})")
                print(f"  종료 MV: {end_mv:,.0f}")
                print(f"  수익률: {return_str}")
                print(f"  기여도 (방법1): {contrib1:.4f}")
                print(f"  기여도 (방법2): {contrib2:.4f}")
                
                if start_pos:
                    print(f"  수량/평단: {start_pos.quantity}/{start_pos.avg_price}")
                if end_pos:
                    print(f"  수량/평단: {end_pos.quantity}/{end_pos.avg_price}")
        
        print(f"\n총 기여도 합계: {total_contrib:.4f}")
        print(f"실제 포트폴리오 수익률: {total_return:.4f}")
        print(f"차이: {abs(total_contrib - total_return):.6f}")
        
    except Exception as e:
        print(f"디버그 중 오류: {e}")
    finally:
        session.close()


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
      asset_df, class_df: 자산별, 자산군별 기여도 데이터프레임
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
                PortfolioPositionDaily.as_of_date >= start_date
            )
        ).scalar()
        end_snap = session.execute(
            select(func.max(PortfolioPositionDaily.as_of_date))
            .where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).scalar()

        if not start_snap or not end_snap:
            print(f"No position data in range {start_date} ~ {end_date}")
            return pd.DataFrame(), pd.DataFrame()

        # 3) starting positions and NAV
        start_pos = session.execute(
            select(
                PortfolioPositionDaily.asset_id,
                PortfolioPositionDaily.market_value,
                PortfolioPositionDaily.quantity,
                PortfolioPositionDaily.avg_price
            ).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date == start_snap
            )
        ).all()

        start_nav = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == pid,
                PortfolioNavDaily.as_of_date == start_snap
            )
        ).scalar()

        if not start_nav or start_nav == 0:
            print(f"No valid starting NAV at {start_snap}")
            return pd.DataFrame(), pd.DataFrame()

        # 4) ending positions and NAV
        end_pos = session.execute(
            select(
                PortfolioPositionDaily.asset_id,
                PortfolioPositionDaily.market_value,
                PortfolioPositionDaily.quantity,
                PortfolioPositionDaily.avg_price
            ).where(
                PortfolioPositionDaily.portfolio_id == pid,
                PortfolioPositionDaily.as_of_date == end_snap
            )
        ).all()

        end_nav = session.execute(
            select(PortfolioNavDaily.nav)
            .where(
                PortfolioNavDaily.portfolio_id == pid,
                PortfolioNavDaily.as_of_date == end_snap
            )
        ).scalar()

        if not end_nav or end_nav == 0:
            print(f"No valid ending NAV at {end_snap}")
            return pd.DataFrame(), pd.DataFrame()

        print(f"Using snapshots: {start_snap} -> {end_snap}")
        print(f"NAV: {start_nav:,.0f} -> {end_nav:,.0f}")

        # 5) build asset-level data
        start_dict = {row.asset_id: {'mv': float(row.market_value), 'qty': float(row.quantity or 0), 'avg_price': float(row.avg_price or 0)} for row in start_pos}
        end_dict = {row.asset_id: {'mv': float(row.market_value), 'qty': float(row.quantity or 0), 'avg_price': float(row.avg_price or 0)} for row in end_pos}

        all_assets = set(start_dict.keys()) | set(end_dict.keys())
        if not all_assets:
            print("No assets found in the position data")
            return pd.DataFrame(), pd.DataFrame()

        asset_data = []
        print(f"\n=== 자산별 계산 디버그 ===")
        for aid in all_assets:
            start_info = start_dict.get(aid, {'mv': 0, 'qty': 0, 'avg_price': 0})
            end_info = end_dict.get(aid, {'mv': 0, 'qty': 0, 'avg_price': 0})
            
            start_mv = start_info['mv']
            end_mv = end_info['mv']
            
            # 더 정확한 기여도 계산 방식
            # 기여도 = (종료 시장가치 - 시작 시장가치) / 시작 NAV
            contrib_pct = (end_mv - start_mv) / float(start_nav)
            
            # 자산 수익률 계산 (정확한 방식)
            if start_mv > 0:
                # 기존 포지션: 일반적인 수익률 계산
                asset_return = (end_mv - start_mv) / start_mv
                weight = start_mv / float(start_nav)
                return_str = f"{asset_return:.4f}"
            elif end_mv > 0:
                # 신규 편입: 편입 시점을 찾아서 정확한 수익률 계산
                # 편입 시점 찾기 (분석 기간 내에서 처음 포지션이 생긴 날)
                entry_date = session.execute(
                    select(func.min(PortfolioPositionDaily.as_of_date))
                    .where(
                        PortfolioPositionDaily.portfolio_id == pid,
                        PortfolioPositionDaily.asset_id == aid,
                        PortfolioPositionDaily.as_of_date >= start_snap,
                        PortfolioPositionDaily.as_of_date <= end_snap,
                        PortfolioPositionDaily.market_value > 0
                    )
                ).scalar()
                
                if entry_date:
                    # 편입 시점의 평균가격 조회
                    entry_pos = session.execute(
                        select(
                            PortfolioPositionDaily.avg_price,
                            PortfolioPositionDaily.quantity
                        ).where(
                            PortfolioPositionDaily.portfolio_id == pid,
                            PortfolioPositionDaily.asset_id == aid,
                            PortfolioPositionDaily.as_of_date == entry_date
                        )
                    ).first()
                    
                    if entry_pos and entry_pos.avg_price and end_info['qty'] > 0:
                        current_price = end_mv / end_info['qty']
                        asset_return = (current_price - float(entry_pos.avg_price)) / float(entry_pos.avg_price)
                        return_str = f"{asset_return:.4f}(NEW@{entry_date})"
                    else:
                        asset_return = 0
                        return_str = f"NEW@{entry_date}(No Price)"
                else:
                    asset_return = 0
                    return_str = "NEW(No Entry Date)"
                weight = 0
            else:
                # 매도된 포지션 - 매도 시점의 가격으로 수익률 계산
                if start_mv > 0:
                    # 매도 시점 찾기
                    exit_date = session.execute(
                        select(func.max(PortfolioPositionDaily.as_of_date))
                        .where(
                            PortfolioPositionDaily.portfolio_id == pid,
                            PortfolioPositionDaily.asset_id == aid,
                            PortfolioPositionDaily.as_of_date >= start_snap,
                            PortfolioPositionDaily.as_of_date <= end_snap,
                            PortfolioPositionDaily.market_value > 0
                        )
                    ).scalar()
                    
                    if exit_date:
                        # 매도 시점 포지션 조회
                        exit_pos = session.execute(
                            select(
                                PortfolioPositionDaily.market_value,
                                PortfolioPositionDaily.quantity
                            ).where(
                                PortfolioPositionDaily.portfolio_id == pid,
                                PortfolioPositionDaily.asset_id == aid,
                                PortfolioPositionDaily.as_of_date == exit_date
                            )
                        ).first()
                        
                        if exit_pos and start_info['avg_price'] > 0:
                            exit_mv = float(exit_pos.market_value)
                            exit_qty = float(exit_pos.quantity)
                            exit_price = exit_mv / exit_qty if exit_qty > 0 else 0
                            start_price = start_info['avg_price']
                            
                            asset_return = (exit_price - start_price) / start_price if start_price > 0 else 0
                            return_str = f"{asset_return:.4f}(SOLD@{exit_date})"
                        else:
                            asset_return = 0
                            return_str = f"SOLD@{exit_date}(No Price)"
                    else:
                        asset_return = 0
                        return_str = "SOLD(No Exit Date)"
                else:
                    asset_return = 0
                    return_str = "SOLD"
                    
                weight = start_mv / float(start_nav) if start_mv > 0 else 0

            # 디버그 출력 (상위/하위 기여자만)
            if abs(contrib_pct) > 0.001:  # 0.1% 이상인 경우만 출력
                print(f"Asset {aid}: start_mv={start_mv:,.0f}, end_mv={end_mv:,.0f}, "
                      f"return={return_str}, weight={weight:.4f}, contrib={contrib_pct:.4f}")

            asset_data.append({
                'asset_id': aid,
                'start_mv': start_mv,
                'end_mv': end_mv,
                'weight': weight,
                'return': asset_return,
                'contrib_pct': contrib_pct
            })

        asset_df = pd.DataFrame(asset_data)
        if asset_df.empty:
            print("No asset data computed")
            return pd.DataFrame(), pd.DataFrame()

        # 6) get asset names and classes
        asset_info = session.execute(
            select(Asset.id, Asset.name, Asset.asset_class)
            .where(Asset.id.in_(list(all_assets)))
        ).all()

        asset_map = {row.id: {'name': row.name, 'asset_class': row.asset_class} 
                    for row in asset_info}

        asset_df['name'] = asset_df['asset_id'].map(lambda x: asset_map.get(x, {}).get('name', f'Asset_{x}'))
        asset_df['asset_class'] = asset_df['asset_id'].map(lambda x: asset_map.get(x, {}).get('asset_class', 'UNKNOWN'))

        # 디버그: 이상한 수익률을 보이는 자산들 찾기
        print(f"\n=== 수익률 검증 ===")
        suspicious_assets = asset_df[
            (asset_df['return'].abs() > 2) |  # 200% 이상 수익률
            (asset_df['return'] < -0.9) |     # -90% 이하 손실률
            (asset_df['contrib_pct'].abs() > 0.05)  # 5% 이상 기여도
        ].sort_values('contrib_pct', ascending=False)
        
        if not suspicious_assets.empty:
            print("의심스러운 자산들:")
            for _, row in suspicious_assets.iterrows():
                print(f"  {row['name']}: return={row['return']:.4f}, contrib={row['contrib_pct']:.4f}, "
                      f"weight={row['weight']:.4f}")
        
        # Top/Bottom 기여자 출력
        print(f"\n=== Top 5 기여자 ===")
        top_5 = asset_df.nlargest(5, 'contrib_pct')
        for _, row in top_5.iterrows():
            print(f"  {row['name']}: {row['contrib_pct']:.4f} ({row['return']:.4f})")
            
        print(f"\n=== Bottom 5 기여자 ===")
        bottom_5 = asset_df.nsmallest(5, 'contrib_pct')
        for _, row in bottom_5.iterrows():
            print(f"  {row['name']}: {row['contrib_pct']:.4f} ({row['return']:.4f})")
            
        # 기여도 합계 검증
        total_contrib = asset_df['contrib_pct'].sum()
        actual_return = (float(end_nav) - float(start_nav)) / float(start_nav)
        print(f"\n=== 기여도 검증 ===")
        print(f"기여도 합계: {total_contrib:.6f}")
        print(f"실제 수익률: {actual_return:.6f}")
        print(f"차이: {abs(total_contrib - actual_return):.6f}")
        
        if abs(total_contrib - actual_return) > 0.001:
            print("⚠️  기여도 합계와 실제 수익률에 차이가 있습니다!")

        # 7) aggregate by asset class
        class_df = asset_df.groupby('asset_class').agg({
            'weight': 'sum',
            'contrib_pct': 'sum',
            'return': lambda x: (asset_df[asset_df['asset_class'] == x.name]['contrib_pct'].sum() / 
                               asset_df[asset_df['asset_class'] == x.name]['weight'].sum()
                               if asset_df[asset_df['asset_class'] == x.name]['weight'].sum() > 0 else 0)
        }).reset_index()

        # Fix the return calculation for asset classes
        for i, row in class_df.iterrows():
            class_assets = asset_df[asset_df['asset_class'] == row['asset_class']]
            if row['weight'] > 0:
                class_df.at[i, 'return'] = class_assets['contrib_pct'].sum() / row['weight']

        print(f"Analysis complete: {len(asset_df)} assets, {len(class_df)} asset classes")
        
        return asset_df.sort_values('contrib_pct', ascending=False), class_df.sort_values('contrib_pct', ascending=False)

    except Exception as e:
        print(f"Error in period_attribution: {e}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        session.close()


def plot_attribution_summary(asset_df: pd.DataFrame, class_df: pd.DataFrame, 
                           portfolio_name: str, start_date: date, end_date: date):
    """기여도 분석 결과 종합 시각화
    
    Args:
        asset_df: 자산별 기여도 데이터프레임
        class_df: 자산군별 기여도 데이터프레임
        portfolio_name: 포트폴리오 이름
        start_date: 시작일
        end_date: 종료일
    """
    if asset_df.empty or class_df.empty:
        print("No data to visualize")
        return
    
    # 데이터 타입 변환
    asset_df['contrib_pct'] = asset_df['contrib_pct'].astype(float)
    class_df['contrib_pct'] = class_df['contrib_pct'].astype(float)
    
    # 2x2 서브플롯 생성
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{portfolio_name} Attribution Analysis ({start_date} ~ {end_date})', 
                 fontsize=16, fontweight='bold')
    
    # 1. Top 5 기여자
    top_assets = asset_df.nlargest(5, 'contrib_pct')
    bars1 = ax1.bar(range(len(top_assets)), top_assets['contrib_pct']*100, 
                    color='green', alpha=0.7)
    ax1.set_title("Top 5 Asset Contributors", fontweight='bold')
    ax1.set_ylabel("Contribution (%)")
    ax1.set_xticks(range(len(top_assets)))
    ax1.set_xticklabels(top_assets['name'], rotation=45, ha='right')
    annotate_bars(ax1, bars1)
    
    # 2. Bottom 5 저해자
    bottom_assets = asset_df.nsmallest(5, 'contrib_pct')
    bars2 = ax2.bar(range(len(bottom_assets)), bottom_assets['contrib_pct']*100, 
                    color='red', alpha=0.7)
    ax2.set_title("Top 5 Asset Detractors", fontweight='bold')
    ax2.set_ylabel("Contribution (%)")
    ax2.set_xticks(range(len(bottom_assets)))
    ax2.set_xticklabels(bottom_assets['name'], rotation=45, ha='right')
    annotate_bars(ax2, bars2)
    
    # 3. 자산군별 기여도
    bars3 = ax3.bar(range(len(class_df)), class_df['contrib_pct']*100, 
                    color='blue', alpha=0.7)
    ax3.set_title("Asset Class Contributions", fontweight='bold')
    ax3.set_ylabel("Contribution (%)")
    ax3.set_xticks(range(len(class_df)))
    ax3.set_xticklabels(class_df['asset_class'], rotation=45, ha='right')
    annotate_bars(ax3, bars3)
    
    # 4. 기여도 분포 히스토그램
    ax4.hist(asset_df['contrib_pct']*100, bins=20, alpha=0.7, color='purple', edgecolor='black')
    ax4.set_title("Contribution Distribution", fontweight='bold')
    ax4.set_xlabel("Contribution (%)")
    ax4.set_ylabel("Frequency")
    ax4.axvline(0, color='red', linestyle='--', alpha=0.8, label='Zero Line')
    ax4.legend()
    
    plt.tight_layout()
    plt.show()


def plot_top_contributors(asset_df: pd.DataFrame, n: int = 10, 
                         title_suffix: str = ""):
    """Top N 기여자 차트"""
    if asset_df.empty:
        print("No data to plot")
        return
    
    asset_df['contrib_pct'] = asset_df['contrib_pct'].astype(float)
    top_assets = asset_df.nlargest(n, 'contrib_pct')
    
    plt.figure(figsize=(12, 8))
    bars = plt.bar(range(len(top_assets)), top_assets['contrib_pct']*100, 
                   color='green', alpha=0.7)
    plt.title(f"Top {n} Asset Contributors {title_suffix}", fontweight='bold', fontsize=14)
    plt.ylabel("Contribution (%)", fontsize=12)
    plt.xticks(range(len(top_assets)), top_assets['name'], rotation=45, ha='right')
    annotate_bars(plt.gca(), bars)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_asset_class_attribution(class_df: pd.DataFrame, title_suffix: str = ""):
    """자산군별 기여도 차트"""
    if class_df.empty:
        print("No data to plot")
        return
        
    class_df['contrib_pct'] = class_df['contrib_pct'].astype(float)
    
    plt.figure(figsize=(12, 6))
    colors = ['green' if x >= 0 else 'red' for x in class_df['contrib_pct']]
    bars = plt.bar(range(len(class_df)), class_df['contrib_pct']*100, 
                   color=colors, alpha=0.7)
    plt.title(f"Asset Class Contributions {title_suffix}", fontweight='bold', fontsize=14)
    plt.ylabel("Contribution (%)", fontsize=12)
    plt.xticks(range(len(class_df)), class_df['asset_class'], rotation=30, ha='right')
    plt.axhline(0, color='black', linestyle='-', alpha=0.3)
    annotate_bars(plt.gca(), bars)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_attribution_waterfall(asset_df: pd.DataFrame, top_n: int = 10):
    """Waterfall 차트로 기여도 시각화"""
    if asset_df.empty:
        print("No data to plot")
        return
    
    asset_df['contrib_pct'] = asset_df['contrib_pct'].astype(float)
    
    # Top N과 Bottom N 선택
    sorted_df = asset_df.sort_values('contrib_pct', ascending=False)
    top_bottom = pd.concat([
        sorted_df.head(top_n//2),
        sorted_df.tail(top_n//2)
    ])
    
    # 기타 항목 추가
    others_contrib = asset_df[~asset_df.index.isin(top_bottom.index)]['contrib_pct'].sum()
    if others_contrib != 0:
        others_row = pd.DataFrame({
            'name': ['Others'],
            'contrib_pct': [others_contrib]
        })
        top_bottom = pd.concat([top_bottom, others_row], ignore_index=True)
    
    # Waterfall 차트 생성
    plt.figure(figsize=(14, 8))
    
    cumsum = 0
    x_pos = []
    heights = []
    colors = []
    
    for i, (_, row) in enumerate(top_bottom.iterrows()):
        contrib = row['contrib_pct'] * 100
        x_pos.append(i)
        heights.append(contrib)
        colors.append('green' if contrib >= 0 else 'red')
        
        # 누적 표시용 점선
        if i > 0:
            plt.plot([i-0.4, i-0.4], [cumsum, cumsum + contrib], 
                    color='gray', linestyle='--', alpha=0.5)
        
        cumsum += contrib
    
    bars = plt.bar(x_pos, heights, color=colors, alpha=0.7, width=0.8)
    plt.title("Attribution Waterfall Chart", fontweight='bold', fontsize=14)
    plt.ylabel("Contribution (%)", fontsize=12)
    plt.xticks(x_pos, top_bottom['name'], rotation=45, ha='right')
    plt.axhline(0, color='black', linestyle='-', alpha=0.3)
    annotate_bars(plt.gca(), bars)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    # 사용 예시
    portfolio_name = "Core"
    start_date = date(2025, 7, 1)
    end_date = date(2025, 8, 26)
    
    # 기여도 분석 수행
    asset_df, class_df = period_attribution(portfolio_name, start_date, end_date)
    
    if not asset_df.empty:
        print("=== 자산별 기여도 Top 10 ===")
        print(asset_df.head(10)[['name', 'weight', 'return', 'contrib_pct']])
        
        print("\n=== 자산군별 기여도 ===")
        print(class_df[['asset_class', 'weight', 'return', 'contrib_pct']])
        
        # 특정 자산 상세 분석 (수익률이 낮은 자산들)
        print("\n" + "="*50)
        print("특정 자산 상세 분석")
        print("="*50)
        
        # 기여도가 낮은 상위 3개 자산 분석
        bottom_assets = asset_df.nsmallest(3, 'contrib_pct')
        for _, row in bottom_assets.iterrows():
            print(f"\n### {row['name']} 분석 ###")
            analyze_specific_asset(portfolio_name, row['name'], start_date, end_date)
        
        # 종합 시각화
        plot_attribution_summary(asset_df, class_df, portfolio_name, start_date, end_date)
        
        # 개별 차트들
        plot_top_contributors(asset_df, 10, f"({start_date} ~ {end_date})")
        plot_asset_class_attribution(class_df, f"({start_date} ~ {end_date})")
        plot_attribution_waterfall(asset_df, 10)

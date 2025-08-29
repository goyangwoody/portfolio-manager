"""
Attribution analysis services - TWR (Time-Weighted Return) calculations
"""
from typing import List, Dict
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import get_db
from utils import safe_float
from schemas import (
    AssetContribution, AssetClassContribution, DailyPortfolioReturn, 
    AssetWeightTrend, AssetReturnTrend, AssetDetailResponse, 
    PricePerformancePoint, AssetFilter
)
from src.pm.db.models import (
    PortfolioPositionDaily, Asset, Price, PortfolioNavDaily, Portfolio
)

def calculate_twr_attribution(
    db: Session, 
    portfolio_id: int, 
    start_date: date, 
    end_date: date
) -> dict:
    """
    TWR(Time-Weighted Return) 기반 포트폴리오 기여도 분석
    
    TWR 계산 공식:
    - w_{i,t-1} = MV_{i,t-1} / Σ_j MV_{j,t-1} (전일 비중)
    - r_{i,t} = P_{i,t} / P_{i,t-1} - 1 (자산 수익률)
    - r_{p,t} = Σ_i w_{i,t-1} * r_{i,t} (포트폴리오 일별 수익률)
    - Contrib_i = Σ_t (w_{i,t-1} * r_{i,t}) (자산별 기여도)
    - R_{period} = ∏_{t}(1+r_{p,t}) - 1 (기간 TWR)
    """
    try:
        # 1. 기간 내 모든 포지션 데이터 조회
        positions = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.as_of_date >= start_date,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).order_by(PortfolioPositionDaily.as_of_date).all()
        
        if not positions:
            raise ValueError("No position data found for the specified period")
        
        # 2. 날짜별로 포지션 데이터 그룹화
        positions_by_date = {}
        all_asset_ids = set()
        
        for pos in positions:
            date_key = pos.as_of_date
            if date_key not in positions_by_date:
                positions_by_date[date_key] = {}
            
            positions_by_date[date_key][pos.asset_id] = {
                'quantity': float(pos.quantity or 0),
                'market_value': float(pos.market_value or 0),
                'asset_id': pos.asset_id
            }
            all_asset_ids.add(pos.asset_id)
        
        # 3. 자산 정보 조회
        assets = db.query(Asset).filter(Asset.id.in_(all_asset_ids)).all()
        asset_info = {asset.id: asset for asset in assets}
        
        # 4. 가격 데이터 조회
        prices = db.query(Price).filter(
            and_(
                Price.asset_id.in_(all_asset_ids),
                Price.date >= start_date,
                Price.date <= end_date
            )
        ).order_by(Price.date).all()
        
        # 가격 데이터를 (asset_id, date) 키로 정리
        price_data = {}
        for price in prices:
            price_data[(price.asset_id, price.date)] = float(price.close)
        
        # 5. 일별 TWR 계산
        sorted_dates = sorted(positions_by_date.keys())
        daily_returns = []
        asset_contributions = {asset_id: 0.0 for asset_id in all_asset_ids}
        
        for i, current_date in enumerate(sorted_dates):
            if i == 0:
                # 첫날은 수익률 계산 불가
                daily_returns.append(DailyPortfolioReturn(
                    date=current_date,
                    daily_return=0.0,
                    portfolio_value=sum(pos['market_value'] for pos in positions_by_date[current_date].values())
                ))
                continue
            
            prev_date = sorted_dates[i-1]
            current_positions = positions_by_date[current_date]
            prev_positions = positions_by_date[prev_date]
            
            # 전일 총 포트폴리오 가치 계산
            prev_total_mv = sum(pos['market_value'] for pos in prev_positions.values())
            
            if prev_total_mv <= 0:
                continue
            
            # 자산별 기여도 계산
            daily_portfolio_return = 0.0
            
            for asset_id in all_asset_ids:
                # 전일 비중 계산
                prev_mv = prev_positions.get(asset_id, {}).get('market_value', 0.0)
                weight_prev = prev_mv / prev_total_mv if prev_total_mv > 0 else 0.0
                
                # 자산 수익률 계산
                prev_price = price_data.get((asset_id, prev_date))
                curr_price = price_data.get((asset_id, current_date))
                
                if prev_price and curr_price and prev_price > 0:
                    prev_price_float = float(prev_price)
                    curr_price_float = float(curr_price)
                    asset_return = (curr_price_float / prev_price_float) - 1
                else:
                    asset_return = 0.0
                
                # 기여도 계산 및 누적
                contribution = weight_prev * asset_return
                asset_contributions[asset_id] += contribution
                daily_portfolio_return += contribution
            
            # 현재 포트폴리오 가치
            current_total_mv = sum(pos['market_value'] for pos in current_positions.values())
            
            daily_returns.append(DailyPortfolioReturn(
                date=current_date,
                daily_return=daily_portfolio_return * 100,  # 퍼센트로 변환
                portfolio_value=current_total_mv
            ))
        
        # 6. 총 TWR 계산
        total_twr = 1.0
        for dr in daily_returns:
            if dr.daily_return is not None:
                total_twr *= (1 + dr.daily_return / 100)
        total_twr = (total_twr - 1) * 100  # 퍼센트로 변환
        
        # 7. 자산별 상세 데이터 생성
        asset_details = []
        for asset_id, contribution in asset_contributions.items():
            if asset_id not in asset_info:
                continue
                
            asset = asset_info[asset_id]
            
            # 평균 비중 계산
            total_weight = 0.0
            weight_count = 0
            
            for date_key in sorted_dates[:-1]:  # 마지막 날 제외 (전일 비중 기준)
                positions = positions_by_date[date_key]
                total_mv = sum(pos['market_value'] for pos in positions.values())
                
                if total_mv > 0:
                    asset_mv = positions.get(asset_id, {}).get('market_value', 0.0)
                    weight = asset_mv / total_mv
                    total_weight += weight
                    weight_count += 1
            
            avg_weight = (total_weight / weight_count * 100) if weight_count > 0 else 0.0
            
            # 자산 기간 수익률 계산
            first_price = price_data.get((asset_id, sorted_dates[0]))
            last_price = price_data.get((asset_id, sorted_dates[-1]))
            if first_price and last_price and first_price > 0:
                first_price_float = float(first_price)
                last_price_float = float(last_price)
                asset_return = ((last_price_float / first_price_float) - 1) * 100
            else:
                asset_return = 0.0
            
            # 현재 allocation 계산 (가장 최근 날짜 기준)
            latest_date = sorted_dates[-1]
            latest_positions = positions_by_date[latest_date]
            total_latest_mv = sum(pos['market_value'] for pos in latest_positions.values())
            current_asset_mv = latest_positions.get(asset_id, {}).get('market_value', 0.0)
            current_allocation = (current_asset_mv / total_latest_mv * 100) if total_latest_mv > 0 else 0.0
            
            print(f"Asset {asset_id}: mv={current_asset_mv}, total_mv={total_latest_mv}, allocation={current_allocation}%")
            
            asset_detail = AssetContribution(
                asset_id=asset_id,
                ticker=asset.ticker or "",
                name=asset.name or asset.ticker or f"Asset_{asset_id}",
                asset_class=asset.asset_class or "Unknown",
                current_allocation=current_allocation,
                avg_weight=avg_weight,
                period_return=asset_return,
                contribution=contribution * 100  # 퍼센트로 변환
            )
            asset_details.append(asset_detail)
        
        # 8. 자산클래스별 기여도 집계
        asset_class_contributions = {}
        for asset in asset_details:
            ac = asset.asset_class
            if ac not in asset_class_contributions:
                asset_class_contributions[ac] = {
                    'contribution': 0.0,
                    'avg_weight': 0.0,
                    'assets': []
                }
            
            asset_class_contributions[ac]['contribution'] += asset.contribution
            asset_class_contributions[ac]['avg_weight'] += asset.avg_weight
            asset_class_contributions[ac]['assets'].append(asset)
        
        # AssetClassContribution 객체로 변환
        asset_class_list = []
        for ac_name, ac_data in asset_class_contributions.items():
            asset_class_list.append(AssetClassContribution(
                asset_class=ac_name,
                avg_weight=ac_data['avg_weight'],
                contribution=ac_data['contribution'],
                assets=ac_data['assets']
            ))
        
        # 9. 상위/하위 기여자 분류
        sorted_assets = sorted(asset_details, key=lambda x: x.contribution, reverse=True)
        top_contributors = [asset for asset in sorted_assets if asset.contribution > 0]
        top_detractors = [asset for asset in sorted_assets if asset.contribution < 0]
        
        # 10. 검증: 총 기여도 합계
        total_contribution_check = sum(asset.contribution for asset in asset_details)
        
        return {
            "total_twr": total_twr,
            "daily_returns": daily_returns,
            "asset_class_contributions": asset_class_list,
            "top_contributors": top_contributors,
            "top_detractors": top_detractors,
            "total_contribution_check": total_contribution_check
        }
        
    except Exception as e:
        print(f"Error in calculate_twr_attribution: {e}")
        raise e

def calculate_detailed_twr_attribution(
    db: Session, 
    portfolio_id: int, 
    start_date: date, 
    end_date: date,
    asset_filter: AssetFilter = AssetFilter.ALL
) -> dict:
    """
    상세한 TWR 기반 포트폴리오 기여도 분석 (차트 데이터 포함)
    
    Features:
    - domestic/foreign 필터링
    - 자산클래스별 차트 데이터 (비중 추이, TWR 추이)
    - 개별 자산 상세 데이터
    """
    try:
        # 1. 기간 내 모든 포지션 데이터 조회
        positions_query = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.as_of_date >= start_date,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        )
        
        # 자산 필터 적용
        if asset_filter != AssetFilter.ALL:
            # Asset 테이블과 조인하여 필터링
            positions_query = positions_query.join(Asset).filter(
                Asset.region == asset_filter.value if asset_filter.value in ["domestic", "foreign"] else True
            )
        
        positions = positions_query.order_by(PortfolioPositionDaily.as_of_date).all()
        
        if not positions:
            raise ValueError("No position data found for the specified period and filter")
        
        # 2. 기본 TWR 계산 수행
        basic_result = calculate_twr_attribution(db, portfolio_id, start_date, end_date)
        
        # 3. 자산 정보와 region 정보 조회
        all_asset_ids = set(pos.asset_id for pos in positions)
        assets = db.query(Asset).filter(Asset.id.in_(all_asset_ids)).all()
        asset_info = {asset.id: asset for asset in assets}
        
        # 4. 자산 필터 재적용 (계산된 결과에서)
        filtered_assets = []
        for asset_detail in basic_result["top_contributors"] + basic_result["top_detractors"]:
            asset = asset_info.get(asset_detail.asset_id)
            if asset:
                # region 정보 추가
                asset_detail.region = getattr(asset, "region", "unknown")
                
                # 필터링 조건 확인
                if asset_filter == AssetFilter.ALL:
                    filtered_assets.append(asset_detail)
                elif asset_filter == AssetFilter.DOMESTIC and asset_detail.region == "domestic":
                    filtered_assets.append(asset_detail)
                elif asset_filter == AssetFilter.FOREIGN and asset_detail.region == "foreign":
                    filtered_assets.append(asset_detail)
        
        # 5. 자산클래스별 차트 데이터 생성
        enhanced_asset_class_contributions = []
        
        # 날짜별로 포지션 데이터 그룹화
        positions_by_date = {}
        for pos in positions:
            date_key = pos.as_of_date
            if date_key not in positions_by_date:
                positions_by_date[date_key] = {}
            positions_by_date[date_key][pos.asset_id] = pos
        
        sorted_dates = sorted(positions_by_date.keys())
        
        # 자산클래스별 데이터 구성
        asset_class_data = {}
        for asset_detail in filtered_assets:
            asset = asset_info.get(asset_detail.asset_id)
            if not asset:
                continue
                
            asset_class = asset.asset_class or "Unknown"
            if asset_class not in asset_class_data:
                asset_class_data[asset_class] = {
                    "assets": [],
                    "weight_trend": [],
                    "return_trend": [],
                    "total_contribution": 0.0,
                    "total_avg_weight": 0.0,
                    "current_allocation": 0.0
                }
            
            # 자산 추가
            asset_class_data[asset_class]["assets"].append(asset_detail)
            asset_class_data[asset_class]["total_contribution"] += asset_detail.contribution
            asset_class_data[asset_class]["total_avg_weight"] += asset_detail.avg_weight
        
        # 자산클래스별 차트 데이터 계산
        for asset_class, data in asset_class_data.items():
            weight_trend = []
            return_trend = []
            cumulative_return = 0.0
            
            for i, date_key in enumerate(sorted_dates):
                # 해당 날짜의 자산클래스 총 비중 계산
                class_total_mv = 0.0
                portfolio_total_mv = 0.0
                
                for pos in positions_by_date[date_key].values():
                    portfolio_total_mv += float(pos.market_value or 0)
                    
                    asset = asset_info.get(pos.asset_id)
                    if asset and (asset.asset_class or "Unknown") == asset_class:
                        class_total_mv += float(pos.market_value or 0)
                
                weight_pct = (class_total_mv / portfolio_total_mv * 100) if portfolio_total_mv > 0 else 0.0
                weight_trend.append(AssetWeightTrend(date=date_key, weight=weight_pct))
                
                # 자산클래스별 TWR 계산
                if i == 0:
                    daily_return = 0.0
                    base_value = class_total_mv
                else:
                    # 전일 대비 자산클래스 가치 변화 계산
                    prev_date = sorted_dates[i-1]
                    prev_class_total_mv = 0.0
                    
                    for pos in positions_by_date[prev_date].values():
                        asset = asset_info.get(pos.asset_id)
                        if asset and (asset.asset_class or "Unknown") == asset_class:
                            prev_class_total_mv += float(pos.market_value or 0)
                    
                    # 일별 수익률 계산 (가치 변화 기준)
                    if prev_class_total_mv > 0:
                        daily_return = ((class_total_mv / prev_class_total_mv) - 1) * 100
                    else:
                        daily_return = 0.0
                
                cumulative_return = ((class_total_mv / base_value) - 1) * 100 if (base_value and base_value > 0) else 0.0
                return_trend.append(AssetReturnTrend(
                    date=date_key, 
                    cumulative_twr=cumulative_return,
                    daily_twr=daily_return
                ))
            
            # 현재 배분 (마지막 날 기준)
            current_allocation = weight_trend[-1].weight if weight_trend else 0.0
            
            enhanced_asset_class_contributions.append(AssetClassContribution(
                asset_class=asset_class,
                current_allocation=current_allocation,
                avg_weight=data["total_avg_weight"],
                contribution=data["total_contribution"],
                weight_trend=weight_trend,
                return_trend=return_trend,
                assets=data["assets"]
            ))
        
        # 6. 상위/하위 기여자 분류
        filtered_sorted = sorted(filtered_assets, key=lambda x: x.contribution, reverse=True)
        top_contributors = [asset for asset in filtered_sorted if asset.contribution > 0]
        top_detractors = [asset for asset in filtered_sorted if asset.contribution < 0]
        
        return {
            "total_twr": basic_result["total_twr"],
            "daily_returns": basic_result["daily_returns"],
            "asset_class_contributions": enhanced_asset_class_contributions,
            "top_contributors": top_contributors,
            "top_detractors": top_detractors,
            "total_contribution_check": sum(asset.contribution for asset in filtered_assets)
        }
        
    except Exception as e:
        print(f"Error in calculate_detailed_twr_attribution: {e}")
        raise e

def calculate_asset_detail(
    db: Session,
    portfolio_id: int,
    asset_id: int,
    start_date: date,
    end_date: date
) -> AssetDetailResponse:
    """개별 자산 상세 정보 계산"""
    try:
        # 자산 정보 조회
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # 포지션 데이터 조회
        positions = db.query(PortfolioPositionDaily).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.asset_id == asset_id,
                PortfolioPositionDaily.as_of_date >= start_date,
                PortfolioPositionDaily.as_of_date <= end_date
            )
        ).order_by(PortfolioPositionDaily.as_of_date).all()
        
        if not positions:
            raise ValueError(f"No position data found for asset {asset_id}")
        
        # 가격 데이터 조회
        prices = db.query(Price).filter(
            and_(
                Price.asset_id == asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            )
        ).order_by(Price.date).all()
        
        # 현재 정보 계산
        latest_position = positions[-1]
        latest_price = prices[-1] if prices else None
        
        # 포트폴리오 총 가치 계산
        from sqlalchemy import func
        portfolio_total_mv_decimal = db.query(func.sum(PortfolioPositionDaily.market_value)).filter(
            and_(
                PortfolioPositionDaily.portfolio_id == portfolio_id,
                PortfolioPositionDaily.as_of_date == latest_position.as_of_date
            )
        ).scalar() or 0
        portfolio_total_mv = float(portfolio_total_mv_decimal)
        
        current_allocation = (float(latest_position.market_value or 0) / portfolio_total_mv * 100) if portfolio_total_mv > 0 else 0.0
        current_price = float(latest_price.close) if latest_price and latest_price.close else 0.0
        
        # NAV 수익률 계산 (간단한 가격 변화)
        first_price = prices[0] if prices else None
        first_price_value = float(first_price.close) if (first_price and first_price.close) else 0.0
        nav_return = ((current_price / first_price_value) - 1) * 100 if first_price_value > 0 else 0.0
        
        # TWR 기여도 계산
        # 전체 포트폴리오 TWR 계산에서 해당 자산의 기여도를 구해야 함
        try:
            # 전체 TWR 계산 호출
            full_attribution = calculate_twr_attribution(db, portfolio_id, start_date, end_date)
            
            # 해당 자산의 기여도 찾기
            twr_contribution = 0.0
            for asset_contrib in full_attribution.get("top_contributors", []) + full_attribution.get("top_detractors", []):
                if asset_contrib.asset_id == asset_id:
                    twr_contribution = asset_contrib.contribution
                    print(f"Found TWR contribution for asset {asset_id}: {twr_contribution}%")
                    break
            
            if twr_contribution == 0.0:
                print(f"No TWR contribution found for asset {asset_id}")
                
        except Exception as e:
            print(f"Error calculating TWR contribution for asset {asset_id}: {e}")
            twr_contribution = 0.0
        
        # 가격 성과 차트 데이터
        price_performance = []
        if prices:
            base_price = float(prices[0].close) if (prices[0] and prices[0].close) else 1.0
            for price in prices:
                price_close_value = float(price.close) if price.close else 0.0
                performance = ((price_close_value / base_price) - 1) * 100 if base_price > 0 else 0.0
                price_performance.append(PricePerformancePoint(
                    date=price.date,
                    performance=performance
                ))
        
        return AssetDetailResponse(
            asset_id=asset_id,
            ticker=asset.ticker or "",
            name=asset.name or asset.ticker or f"Asset_{asset_id}",
            asset_class=asset.asset_class or "Unknown",
            region=getattr(asset, "region", "unknown"),
            current_allocation=current_allocation,
            current_price=current_price,
            nav_return=nav_return,
            twr_contribution=twr_contribution,
            price_performance=price_performance
        )
        
    except Exception as e:
        print(f"Error in calculate_asset_detail: {e}")
        raise e

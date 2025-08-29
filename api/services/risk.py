"""
Risk analysis service
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text, desc
from datetime import date as Date, datetime, timedelta
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd

# ORM 모델 import
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pm.db.models import PortfolioPositionDaily, Asset, Price

from schemas.common import AssetFilter, TimePeriod
from schemas.risk import (
    RiskAnalysisResponse,
    PortfolioRiskMetrics,
    AssetRiskContribution,
    CorrelationMatrix,
    AssetCorrelation,
    StressTestResponse,
    StressTestResult,
    StressScenario,
    AssetClassDetailsResponse,
    AssetClassDetailItem
)

class RiskService:
    def __init__(self, db: Session):
        self.db = db

    async def get_asset_allocation(
        self,
        portfolio_id: int,
        as_of_date: Optional[Date] = None,
        asset_filter: AssetFilter = AssetFilter.ALL
    ) -> Dict[str, Any]:
        """
        자산군별 배분 현황을 조회합니다.
        """
        try:
            # 기준일 설정
            if as_of_date is None:
                as_of_date_query = text("""
                    SELECT MAX(as_of_date) 
                    FROM portfolio_positions_daily 
                    WHERE portfolio_id = :portfolio_id
                """)
                result = self.db.execute(as_of_date_query, {"portfolio_id": portfolio_id}).scalar()
                as_of_date = result or datetime.now().date()

            # 자산별 포지션과 자산 정보 조회
            query = text("""
                WITH portfolio_positions AS (
                    SELECT 
                        ppd.asset_id,
                        ppd.quantity,
                        ppd.market_value,
                        ppd.market_value / SUM(ppd.market_value) OVER() * 100 as weight
                    FROM portfolio_positions_daily ppd
                    WHERE ppd.portfolio_id = :portfolio_id 
                        AND ppd.as_of_date = :as_of_date
                        AND ppd.quantity > 0
                )
                SELECT 
                    a.id as asset_id,
                    a.ticker,
                    a.name,
                    a.asset_class,
                    pp.quantity,
                    pp.market_value,
                    pp.weight,
                    SUM(pp.market_value) OVER() as total_portfolio_value
                FROM portfolio_positions pp
                JOIN assets a ON pp.asset_id = a.id
                ORDER BY a.asset_class, pp.market_value DESC
            """)
            
            result = self.db.execute(query, {
                "portfolio_id": portfolio_id,
                "as_of_date": as_of_date
            }).fetchall()

            if not result:
                return {
                    "total_portfolio_value": 0.0,
                    "as_of_date": as_of_date.isoformat(),
                    "allocations": [],
                    "asset_filter": asset_filter.value
                }

            # 자산군별로 그룹화
            asset_class_groups = {}
            total_portfolio_value = 0.0
            
            for row in result:
                asset_class = row.asset_class
                total_portfolio_value = float(row.total_portfolio_value)
                
                if asset_class not in asset_class_groups:
                    asset_class_groups[asset_class] = {
                        "asset_class": asset_class,
                        "total_value": 0.0,
                        "total_weight": 0.0,
                        "asset_count": 0,
                        "assets": []
                    }
                
                asset_info = {
                    "asset_id": row.asset_id,
                    "ticker": row.ticker,
                    "name": row.name,
                    "asset_class": row.asset_class,
                    "quantity": float(row.quantity),
                    "market_value": float(row.market_value),
                    "weight": float(row.weight)
                }
                
                asset_class_groups[asset_class]["assets"].append(asset_info)
                asset_class_groups[asset_class]["total_value"] += asset_info["market_value"]
                asset_class_groups[asset_class]["total_weight"] += asset_info["weight"]
                asset_class_groups[asset_class]["asset_count"] += 1

            allocations = list(asset_class_groups.values())
            
            return {
                "total_portfolio_value": total_portfolio_value,
                "as_of_date": as_of_date.isoformat(),
                "allocations": allocations,
                "asset_filter": asset_filter.value
            }

        except Exception as e:
            print(f"자산 배분 조회 오류: {str(e)}")
            return {
                "total_portfolio_value": 0.0,
                "as_of_date": as_of_date.isoformat() if as_of_date else datetime.now().date().isoformat(),
                "allocations": [],
                "asset_filter": asset_filter.value,
                "error": str(e)
            }

    async def analyze_portfolio_risk(
        self,
        portfolio_id: int,
        period: TimePeriod = TimePeriod.ALL,
        asset_filter: AssetFilter = AssetFilter.ALL,
        confidence_level: float = 0.95
    ) -> RiskAnalysisResponse:
        """
        포트폴리오 리스크 분석을 수행합니다.
        """
        try:
            # 분석 기간 설정 (더미 구현)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)  # 1년
            
            # 일별 포트폴리오 수익률 조회
            daily_returns_query = text("""
                SELECT 
                    nav_date as date,
                    daily_return
                FROM portfolio_nav_daily 
                WHERE portfolio_id = :portfolio_id
                    AND nav_date BETWEEN :start_date AND :end_date
                    AND daily_return IS NOT NULL
                ORDER BY nav_date
            """)
            
            returns_data = self.db.execute(daily_returns_query, {
                "portfolio_id": portfolio_id,
                "start_date": start_date,
                "end_date": end_date
            }).fetchall()

            if len(returns_data) < 30:  # 최소 30일 데이터 필요
                raise Exception("리스크 분석을 위한 충분한 데이터가 없습니다")

            # 포트폴리오 리스크 지표 계산
            daily_returns = [float(row.daily_return) for row in returns_data]
            portfolio_metrics = self._calculate_portfolio_risk_metrics(
                daily_returns, start_date, end_date, confidence_level
            )

            # 자산별 리스크 기여도 계산 (간소화된 버전)
            asset_contributions = await self._calculate_asset_risk_contributions(
                portfolio_id, start_date, end_date, asset_filter
            )

            # 상위 리스크 기여 자산 (상위 5개)
            top_contributors = sorted(
                asset_contributions, 
                key=lambda x: x.risk_contribution, 
                reverse=True
            )[:5]

            return RiskAnalysisResponse(
                portfolio_metrics=portfolio_metrics,
                asset_risk_contributions=asset_contributions,
                top_risk_contributors=top_contributors,
                asset_filter=asset_filter,
                period=period,
                confidence_level=confidence_level,
                total_risk_contribution_check=sum(a.risk_contribution for a in asset_contributions)
            )

        except Exception as e:
            raise Exception(f"리스크 분석 실패: {str(e)}")

    def _calculate_portfolio_risk_metrics(
        self, 
        daily_returns: List[float], 
        start_date: Date, 
        end_date: Date, 
        confidence_level: float
    ) -> PortfolioRiskMetrics:
        """포트폴리오 리스크 지표를 계산합니다."""
        
        returns_array = np.array(daily_returns)
        
        # 연환산 변동성 (252 거래일 기준)
        volatility = np.std(returns_array) * np.sqrt(252) * 100
        
        # 샤프 비율 (무위험수익률 2.5% 가정)
        excess_returns = returns_array - (0.025 / 252)  # 일일 무위험수익률
        sharpe_ratio = np.mean(excess_returns) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
        
        # 최대 낙폭 계산
        cumulative_returns = np.cumprod(1 + returns_array / 100)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max * 100
        max_drawdown = np.min(drawdowns)
        
        # VaR 계산
        var_95 = np.percentile(returns_array, (1 - 0.95) * 100)
        var_99 = np.percentile(returns_array, (1 - 0.99) * 100)
        
        period_days = (end_date - start_date).days
        
        return PortfolioRiskMetrics(
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=abs(max_drawdown),
            var_95=abs(var_95),
            var_99=abs(var_99),
            period_days=period_days,
            start_date=start_date,
            end_date=end_date
        )

    async def _calculate_asset_risk_contributions(
        self,
        portfolio_id: int,
        start_date: Date,
        end_date: Date,
        asset_filter: AssetFilter
    ) -> List[AssetRiskContribution]:
        """자산별 리스크 기여도를 계산합니다 (간소화된 버전)."""
        
        # 최신 포지션 정보 조회
        positions_query = text("""
            WITH latest_positions AS (
                SELECT 
                    p.asset_id,
                    p.market_value,
                    a.ticker,
                    a.name,
                    a.asset_class,
                    pt.total_value
                FROM portfolio_positions_daily p
                JOIN assets a ON p.asset_id = a.id
                CROSS JOIN (
                    SELECT SUM(market_value) as total_value
                    FROM portfolio_positions_daily
                    WHERE portfolio_id = :portfolio_id
                        AND as_of_date = (
                            SELECT MAX(as_of_date) 
                            FROM portfolio_positions_daily 
                            WHERE portfolio_id = :portfolio_id
                        )
                ) pt
                WHERE p.portfolio_id = :portfolio_id
                    AND p.as_of_date = (
                        SELECT MAX(as_of_date) 
                        FROM portfolio_positions_daily 
                        WHERE portfolio_id = :portfolio_id
                    )
                    AND p.quantity > 0
            )
            SELECT *,
                   (market_value / total_value * 100) as current_weight
            FROM latest_positions
            ORDER BY market_value DESC
        """)
        
        positions = self.db.execute(positions_query, {
            "portfolio_id": portfolio_id
        }).fetchall()

        asset_contributions = []
        
        for pos in positions:
            # 간소화된 리스크 기여도 계산 (실제로는 더 복잡한 계산이 필요)
            weight = pos.current_weight
            
            # 자산 변동성 추정 (간소화)
            volatility = max(10.0, weight * 0.5)  # 최소 10%, 비중에 비례한 변동성
            
            # 리스크 기여도 = 비중 * 변동성 비율
            risk_contribution = weight * (volatility / 100)
            
            asset_contributions.append(AssetRiskContribution(
                asset_id=pos.asset_id,
                ticker=pos.ticker,
                name=pos.name or pos.ticker,
                asset_class=pos.asset_class or 'Unknown',
                current_weight=weight,
                volatility=volatility,
                beta=1.0,  # 베타는 1.0으로 가정
                risk_contribution=risk_contribution,
                marginal_var=risk_contribution * 0.1  # 간소화된 한계 VaR
            ))
        
        return asset_contributions

    async def analyze_asset_correlation(
        self,
        portfolio_id: int,
        period: TimePeriod = TimePeriod.ONE_YEAR,
        asset_filter: AssetFilter = AssetFilter.ALL
    ) -> CorrelationMatrix:
        """자산간 상관관계를 분석합니다."""
        
        # 분석 기간 설정 (더미 구현)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)  # 1년
        
        # 현재는 더미 데이터 반환 (실제 구현시 자산별 수익률 데이터 필요)
        correlations = [
            AssetCorrelation(
                asset1_id=1,
                asset1_ticker="AAPL",
                asset2_id=2,
                asset2_ticker="MSFT",
                correlation=0.65
            )
        ]
        
        return CorrelationMatrix(
            asset_correlations=correlations,
            period=period,
            start_date=start_date,
            end_date=end_date,
            asset_filter=asset_filter
        )

    async def run_stress_test(
        self,
        portfolio_id: int,
        scenario: str = "market_crash",
        as_of_date: Optional[Date] = None,
        asset_filter: AssetFilter = AssetFilter.ALL
    ) -> StressTestResponse:
        """스트레스 테스트를 수행합니다."""
        
        if as_of_date is None:
            as_of_date = datetime.now().date()
        
        # 현재는 더미 데이터 반환
        scenario_obj = StressScenario(
            scenario_name="Market Crash",
            description="주식시장 30% 하락 시나리오",
            market_shock=-30.0
        )
        
        stress_result = StressTestResult(
            scenario=scenario_obj,
            portfolio_impact=-15.0,
            value_at_risk=1000000.0,
            asset_impacts=[]
        )
        
        return StressTestResponse(
            stress_results=[stress_result],
            base_portfolio_value=10000000.0,
            as_of_date=as_of_date,
            asset_filter=asset_filter
        )

    async def get_asset_class_details(
        self,
        portfolio_id: int,
        asset_class: str,
        as_of_date: Optional[Date] = None,
        asset_filter: AssetFilter = AssetFilter.ALL
    ) -> Dict[str, Any]:
        """
        특정 자산군의 상세 정보를 조회합니다.
        """
        try:
            # 기준일 설정
            if as_of_date is None:
                as_of_date_query = text("""
                    SELECT MAX(as_of_date) 
                    FROM portfolio_positions_daily 
                    WHERE portfolio_id = :portfolio_id
                """)
                result = self.db.execute(as_of_date_query, {"portfolio_id": portfolio_id}).scalar()
                as_of_date = result or datetime.now().date()

            # 특정 자산군의 자산들 조회
            query = text("""
                WITH portfolio_positions AS (
                    SELECT 
                        ppd.asset_id,
                        ppd.quantity,
                        ppd.market_value,
                        ppd.market_value / SUM(ppd.market_value) OVER() * 100 as weight
                    FROM portfolio_positions_daily ppd
                    WHERE ppd.portfolio_id = :portfolio_id 
                        AND ppd.as_of_date = :as_of_date
                        AND ppd.quantity > 0
                )
                SELECT 
                    a.id as asset_id,
                    a.ticker,
                    a.name,
                    a.asset_class,
                    pp.quantity,
                    pp.market_value,
                    pp.weight,
                    COALESCE(ap.price, 0) as current_price
                FROM portfolio_positions pp
                JOIN assets a ON pp.asset_id = a.id
                LEFT JOIN asset_prices ap ON a.id = ap.asset_id 
                    AND ap.date = (
                        SELECT MAX(date) 
                        FROM asset_prices 
                        WHERE asset_id = a.id 
                        AND date <= :as_of_date
                    )
                WHERE a.asset_class = :asset_class
                ORDER BY pp.market_value DESC
            """)
            
            result = self.db.execute(query, {
                "portfolio_id": portfolio_id,
                "as_of_date": as_of_date,
                "asset_class": asset_class
            }).fetchall()

            if not result:
                return {
                    "asset_class": asset_class,
                    "total_value": 0.0,
                    "total_weight": 0.0,
                    "asset_count": 0,
                    "assets": [],
                    "as_of_date": as_of_date
                }

            # 결과 처리
            assets = []
            total_value = 0.0
            total_weight = 0.0
            
            for row in result:
                asset_info = {
                    "asset_id": row.asset_id,
                    "ticker": row.ticker,
                    "name": row.name,
                    "asset_class": row.asset_class,
                    "quantity": float(row.quantity),
                    "market_value": float(row.market_value),
                    "weight": float(row.weight),
                    "current_price": float(row.current_price)
                }
                assets.append(asset_info)
                total_value += asset_info["market_value"]
                total_weight += asset_info["weight"]

            return {
                "asset_class": asset_class,
                "total_value": total_value,
                "total_weight": total_weight,
                "asset_count": len(assets),
                "assets": assets,
                "as_of_date": as_of_date
            }

        except Exception as e:
            print(f"자산군 상세 정보 조회 오류: {str(e)}")
            return {
                "asset_class": asset_class,
                "total_value": 0.0,
                "total_weight": 0.0,
                "asset_count": 0,
                "assets": [],
                "as_of_date": as_of_date,
                "error": str(e)
            }

    async def get_asset_class_details_new(
        self,
        portfolio_id: int,
        asset_class: str,
        as_of_date: Optional[Date] = None,
        asset_filter: AssetFilter = AssetFilter.ALL
    ) -> AssetClassDetailsResponse:
        """
        특정 자산군의 상세 정보를 조회합니다. (ORM 방식)
        Assets 페이지 형식과 동일한 상세 정보를 제공합니다.
        """
        try:
            # 기준일 설정
            if as_of_date is None:
                latest_date_result = (
                    self.db.query(PortfolioPositionDaily.as_of_date)
                    .filter(PortfolioPositionDaily.portfolio_id == portfolio_id)
                    .order_by(desc(PortfolioPositionDaily.as_of_date))
                    .first()
                )
                as_of_date = latest_date_result[0] if latest_date_result else datetime.now().date()

            # 포지션 정보와 자산 정보 조회
            # 서브쿼리: 포트폴리오 포지션 정보
            positions_query = (
                self.db.query(
                    PortfolioPositionDaily.asset_id,
                    PortfolioPositionDaily.quantity,
                    PortfolioPositionDaily.avg_price,
                    PortfolioPositionDaily.market_value,
                    (PortfolioPositionDaily.market_value / 
                     func.sum(PortfolioPositionDaily.market_value).over() * 100).label('weight')
                )
                .filter(
                    PortfolioPositionDaily.portfolio_id == portfolio_id,
                    PortfolioPositionDaily.as_of_date == as_of_date,
                    PortfolioPositionDaily.quantity > 0
                )
                .subquery()
            )

            # 서브쿼리: 최신 가격 정보
            latest_prices_query = (
                self.db.query(
                    Price.asset_id,
                    Price.close.label('current_price'),
                    Price.date.label('price_date'),
                    func.row_number().over(
                        partition_by=Price.asset_id,
                        order_by=desc(Price.date)
                    ).label('rn')
                )
                .filter(Price.date <= as_of_date)
                .subquery()
            )

            # 서브쿼리: 전일 가격 정보
            prev_day_prices_query = (
                self.db.query(
                    Price.asset_id,
                    Price.close.label('prev_price'),
                    func.row_number().over(
                        partition_by=Price.asset_id,
                        order_by=desc(Price.date)
                    ).label('rn')
                )
                .filter(Price.date < as_of_date)
                .subquery()
            )

            # 메인 쿼리: 자산군에 속한 자산들의 상세 정보
            main_query = (
                self.db.query(
                    Asset.id.label('asset_id'),
                    Asset.ticker,
                    Asset.name,
                    Asset.asset_class,
                    Asset.currency,
                    positions_query.c.quantity,
                    positions_query.c.avg_price,
                    positions_query.c.market_value,
                    positions_query.c.weight,
                    func.coalesce(
                        latest_prices_query.c.current_price,
                        positions_query.c.avg_price
                    ).label('current_price'),
                    func.coalesce(
                        prev_day_prices_query.c.prev_price,
                        positions_query.c.avg_price
                    ).label('prev_price'),
                    func.sum(positions_query.c.market_value).over().label('total_portfolio_value')
                )
                .join(positions_query, Asset.id == positions_query.c.asset_id)
                .outerjoin(
                    latest_prices_query,
                    and_(
                        Asset.id == latest_prices_query.c.asset_id,
                        latest_prices_query.c.rn == 1
                    )
                )
                .outerjoin(
                    prev_day_prices_query,
                    and_(
                        Asset.id == prev_day_prices_query.c.asset_id,
                        prev_day_prices_query.c.rn == 1
                    )
                )
                .filter(Asset.asset_class == asset_class)
                .order_by(desc(positions_query.c.market_value))
            )

            result = main_query.all()

            if not result:
                return AssetClassDetailsResponse(
                    asset_class=asset_class,
                    total_value=0.0,
                    total_weight=0.0,
                    asset_count=0,
                    assets=[],
                    as_of_date=as_of_date,
                    portfolio_id=portfolio_id,
                    avg_return=None,
                    total_unrealized_pnl=None
                )

            # 결과 처리 및 계산
            assets = []
            total_value = 0.0
            total_weight = 0.0
            total_unrealized_pnl = 0.0
            
            for row in result:
                current_price = float(row.current_price)
                avg_price = float(row.avg_price)
                prev_price = float(row.prev_price)
                quantity = float(row.quantity)
                market_value = float(row.market_value)
                
                # 수익률 계산
                day_change = current_price - prev_price if prev_price else 0.0
                day_change_percent = (day_change / prev_price * 100) if prev_price and prev_price > 0 else 0.0
                unrealized_pnl = (current_price - avg_price) * quantity if avg_price else 0.0
                total_return_percent = ((current_price - avg_price) / avg_price * 100) if avg_price and avg_price > 0 else 0.0
                
                asset_detail = AssetClassDetailItem(
                    asset_id=row.asset_id,
                    ticker=row.ticker,
                    name=row.name,
                    asset_class=row.asset_class,
                    region=None,  # region 필드가 없으므로 None으로 설정
                    currency=row.currency,
                    quantity=quantity,
                    avg_price=avg_price,
                    current_price=current_price,
                    market_value=market_value,
                    weight=float(row.weight),
                    day_change=day_change,
                    day_change_percent=day_change_percent,
                    unrealized_pnl=unrealized_pnl,
                    total_return_percent=total_return_percent
                )
                
                assets.append(asset_detail)
                total_value += market_value
                total_weight += float(row.weight)
                total_unrealized_pnl += unrealized_pnl

            # 평균 수익률 계산 (가중평균)
            avg_return = sum(asset.total_return_percent * asset.weight for asset in assets) / total_weight if total_weight > 0 else None

            return AssetClassDetailsResponse(
                asset_class=asset_class,
                total_value=total_value,
                total_weight=total_weight,
                asset_count=len(assets),
                assets=assets,
                as_of_date=as_of_date,
                portfolio_id=portfolio_id,
                avg_return=avg_return,
                total_unrealized_pnl=total_unrealized_pnl
            )

        except Exception as e:
            print(f"자산군 상세 정보 조회 오류: {str(e)}")
            raise Exception(f"자산군 상세 정보 조회 실패: {str(e)}")

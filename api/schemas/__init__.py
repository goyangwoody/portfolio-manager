"""
Schemas package - Consolidated Pydantic models
"""

# ================================
# CORE SCHEMAS
# ================================
from .common import (
    # Enums
    TimePeriod,
    AssetClassFilter,
    RegionFilter,
    
    # Common models
    AssetFilter,
    ErrorResponse,
)

from .portfolio import (
    # Portfolio schemas
    PortfolioListResponse,
    PortfolioSummaryResponse,
    NavChartDataPoint,
    PortfolioWithChartResponse,
    PortfoliosResponse,
)

from .performance import (
    # Performance response schemas
    RecentReturnData,
    DailyReturnPoint,
    BenchmarkReturn,
    PerformanceAllTimeResponse,
    PerformanceCustomPeriodResponse,
    PerformanceDataPoint,
    PerformanceResponse,
)

from .attribution import (
    # TWR-based attribution
    AssetContribution,
    AssetClassContribution,
    AttributionAllTimeResponse,
    AttributionSpecificPeriodResponse,
    AttributionCustomPeriodResponse,
    
    # Asset details and trends
    AssetDetailResponse,
    DailyPortfolioReturn,
    AssetWeightTrend,
    AssetReturnTrend,
    PricePerformancePoint,
)

from .holdings import (
    # Current holdings
    CurrentHolding,
    HoldingsResponse,
    
    # Position snapshots
    PositionSnapshot,
    PositionsResponse,
    
    # Asset allocation
    AssetClassAllocation,
    RegionAllocation,
    AllocationResponse,
    
    # Legacy holdings
    AssetHolding,
    PortfolioHoldingsResponse,
)

from .risk import (
    # Risk analysis
    PortfolioRiskMetrics,
    AssetRiskContribution,
    RiskAnalysisResponse,
    
    # Correlation analysis
    AssetCorrelation,
    CorrelationMatrix,
    
    # Stress testing
    StressScenario,
    StressTestResult,
    StressTestResponse,
    
    # Legacy risk
    VolatilityResponse,
    RiskContributionResponse,
)

from .assets import (
    # Asset information
    AssetInfo,
    AssetDetail,
    AssetsListResponse,
    
    # Asset prices
    PriceHistory,
    AssetPriceResponse,
    
    # Asset search
    AssetSearchCriteria,
    AssetSearchResponse,
    
    # Benchmarks
    BenchmarkInfo,
    BenchmarkPerformance,
    BenchmarkComparisonResponse,
    
    # Legacy assets
    Asset,
)

from .transactions import (
    # Transaction types
    TransactionType,
    TransactionStatus,
    
    # Transaction operations
    TransactionCreate,
    TransactionUpdate,
    Transaction,
    TransactionResponse,
    
    # Transaction summaries
    TransactionSummary,
    AssetTransactionSummary,
    TransactionSummaryResponse,
    
    # Bulk operations
    BulkTransactionCreate,
    BulkTransactionResponse,
    
    # Cash flows
    CashFlow,
    CashFlowResponse,
)

# ================================
# SCHEMA GROUPS
# ================================

# All response schemas for easy import
__all__ = [
    # Common
    "TimePeriod", "AssetClassFilter", "RegionFilter", "AssetFilter", "ErrorResponse",
    
    # Portfolio
    "PortfolioListResponse", "NavChartDataPoint", "PortfolioWithChartResponse", "PortfoliosResponse",
    "PortfolioSummaryResponse",
    
    # Performance
    "RecentReturnData", "DailyReturnPoint", "BenchmarkReturn", 
    "PerformanceAllTimeResponse", "PerformanceCustomPeriodResponse",
    "PerformanceDataPoint", "PerformanceResponse",
    
    # Attribution (TWR-based only)
    "AssetContribution", "AssetClassContribution", "AttributionAllTimeResponse", 
    "AttributionSpecificPeriodResponse", "AttributionCustomPeriodResponse",
    "AssetDetailResponse", "DailyPortfolioReturn", "AssetWeightTrend", 
    "AssetReturnTrend", "PricePerformancePoint",
    
    # Holdings
    "CurrentHolding", "HoldingsResponse", "PositionSnapshot", 
    "AssetClassAllocation", "RegionAllocation", "AllocationResponse",
    "AssetHolding", "PortfolioHoldingsResponse",
    
    # Risk
    "PortfolioRiskMetrics", "AssetRiskContribution", "RiskAnalysisResponse",
    "AssetCorrelation", "CorrelationMatrix",
    "StressScenario", "StressTestResult", "StressTestResponse",
    "VolatilityResponse", "RiskContributionResponse",
    
    # Assets
    "AssetInfo", "AssetDetail", "AssetsListResponse",
    "PriceHistory", "AssetPriceResponse",
    "AssetSearchCriteria", "AssetSearchResponse", 
    "BenchmarkInfo", "BenchmarkPerformance",
    "Asset",
    
    # Transactions
    "TransactionType", "TransactionStatus",
    "TransactionCreate", "TransactionUpdate", "Transaction", "TransactionResponse",
    "TransactionSummary", "AssetTransactionSummary", "TransactionSummaryResponse",
    "BulkTransactionCreate", "BulkTransactionResponse",
    "CashFlow", "CashFlowResponse",
]

"""
Common schemas and enums used across the application
"""
from pydantic import BaseModel
from enum import Enum
from datetime import date
from typing import Optional

# ================================
# COMMON ENUMS & TYPES
# ================================

class TimePeriod(str, Enum):
    """분석 기간 옵션"""
    ALL = "all"                 # 전체 기간 (= INCEPTION)
    INCEPTION = "inception"      # 투자 시작부터
    YTD = "ytd"                 # 연초부터
    ONE_MONTH = "1m"            # 1개월
    THREE_MONTHS = "3m"         # 3개월
    SIX_MONTHS = "6m"           # 6개월
    ONE_YEAR = "1y"             # 1년
    YEAR_1 = "1y"               # Alias for ONE_YEAR
    MONTH_6 = "6m"              # Alias for SIX_MONTHS
    MONTH_3 = "3m"              # Alias for THREE_MONTHS
    MONTH_1 = "1m"              # Alias for ONE_MONTH
    WEEK_1 = "1w"               # 1주

class PortfolioType(str, Enum):
    """포트폴리오 타입"""
    CORE = "core"           # Core 포트폴리오 (ID: 1)
    USD_CORE = "usd_core"   # USD Core 포트폴리오 (ID: 3)

class AssetFilter(str, Enum):
    """자산 필터 옵션"""
    ALL = "all"                 # 전체 자산
    DOMESTIC = "domestic"       # 국내 자산
    FOREIGN = "foreign"         # 해외 자산

class AssetClassFilter(str, Enum):
    """자산 클래스 필터"""
    ALL = "all"
    EQUITY = "equity"
    BOND = "bond"
    REAL_ESTATE = "real_estate"
    COMMODITY = "commodity"

class RegionFilter(str, Enum):
    """지역 필터"""
    ALL = "all"
    DOMESTIC = "domestic"
    FOREIGN = "foreign"

# ================================
# ERROR RESPONSES
# ================================

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

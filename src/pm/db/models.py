import os
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, Enum, ForeignKey, UniqueConstraint, Numeric
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 환경 변수(.env) 로드 시도
try:
    # python-dotenv이 없는 환경에서도 동작하도록 Optional import
    from dotenv import load_dotenv  # type: ignore
    
    # 프로젝트 루트 디렉토리의 .env 파일 경로 찾기
    # 현재 파일(models.py)에서 프로젝트 루트까지의 경로: src/pm/db/models.py -> ../../..
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / '.env'
    
    # .env 파일이 존재하면 로드
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # 프로젝트 루트에 .env가 없으면 기본 동작 (현재 디렉토리에서 찾기)
        load_dotenv()
except Exception:
    # dotenv 미설치 또는 로드 실패 시 무시하고 OS 환경변수만 사용
    pass

# Base 선언: SQLAlchemy ORM 모델의 공통 부모 클래스
Base = declarative_base()

# ENUM 정의
PERIOD_TYPE_ENUM = ('WEEK', 'MONTH', 'QUARTER')
RANK_TYPE_ENUM = ('TOP', 'BOTTOM')

ASSET_CLASS_ENUM = (
    'SP50', 'FXCOM', 'GL_INDEX', 'GL_SECTOR', 'KR_INDEX', 'KR_SECTOR', 'MONEY_ULTRA_SHORT', 'GL_BOND_CORP', 'GL_BOND_AGG', 'KR_BOND_CORP', 'KR_BOND_AGG'
    )


# Portfolio 테이블 모델
class Portfolio(Base):
    __tablename__ = 'portfolios'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    created_at = Column(Date, nullable=False)
    currency   = Column(String(3), nullable=False, default='KRW')
    initial_cash   = Column(Numeric(20,4), nullable=False, default=1000000000.0)
    cash_balance   = Column(Numeric(20,4), nullable=False, default=1000000000.0)
    # 관련 관계
    transactions = relationship("Transaction", back_populates="portfolio")
    performance_data = relationship("PortfolioPerformance", back_populates="portfolio")
    positions_daily = relationship(
        "PortfolioPositionDaily",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    navs_daily = relationship(
        "PortfolioNavDaily",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    asset_class_returns = relationship(
        "AssetClassReturnDaily",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    # 기여도 분석 관련 관계
    asset_attributions = relationship(
        "AssetAttributionPeriodic",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    class_attributions = relationship(
        "AssetClassAttributionPeriodic",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
    attribution_highlights = relationship(
        "AttributionHighlightsPeriodic",
        back_populates="portfolio",
        cascade="all, delete-orphan"
    )
# Asset 테이블 모델
class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    name = Column(String(100))
    currency = Column(String(3), nullable=False, default='KRW')
    asset_class = Column(Enum(*ASSET_CLASS_ENUM, name='asset_class_enum'), nullable=True)  # 새 컬럼

    # 관련 관계
    prices = relationship("Price", back_populates="asset", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="asset")
    positions_daily = relationship(
        "PortfolioPositionDaily",
        back_populates="asset",
        cascade="all, delete-orphan"
    )
# Price 테이블 모델
class Price(Base):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id', ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    close = Column(Numeric(20,8), nullable=False)

    asset = relationship("Asset", back_populates="prices")
    __table_args__ = (
        UniqueConstraint('asset_id', 'date', name='uq_price_asset_date'),
    )


# Transaction 테이블 모델
class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    trans_date = Column(Date, nullable=False)
    quantity = Column(Numeric(20,8), nullable=False)
    price = Column(Numeric(20,8), nullable=False)
    fee = Column(Numeric(20,8),   nullable=False, default=0)
    tax = Column(Numeric(20,8),   nullable=False, default=0)
    type = Column(Enum('BUY', 'SELL',"DEPOSIT", "WITHDRAW", "DIVIDEND", name='transaction_type'), nullable=False)

    # 관계 설정
    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")

class PortfolioPositionDaily(Base):
    __tablename__ = 'portfolio_positions_daily'
    id             = Column(Integer, primary_key=True)
    portfolio_id   = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    as_of_date     = Column(Date, nullable=False)
    asset_id       = Column(Integer, ForeignKey('assets.id'), nullable=False)
    quantity       = Column(Numeric(20,8), nullable=False)
    avg_price      = Column(Numeric(20,8), nullable=False)
    market_value   = Column(Numeric(20,4), nullable=False)  # quantity × close
    
    __table_args__ = (UniqueConstraint('portfolio_id','as_of_date','asset_id',
                         name='uq_posdaily_port_date_asset'),)

    portfolio = relationship("Portfolio", back_populates="positions_daily")
    asset     = relationship("Asset",     back_populates="positions_daily")

class PortfolioNavDaily(Base):
    __tablename__ = 'portfolio_nav_daily'
    id                  = Column(Integer, primary_key=True)
    portfolio_id        = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    as_of_date          = Column(Date, nullable=False)
    cash_balance        = Column(Numeric(20,4), nullable=False)
    total_market_value  = Column(Numeric(20,4), nullable=False)
    nav                 = Column(Numeric(20,4), nullable=False)
    __table_args__ = (
        UniqueConstraint('portfolio_id','as_of_date', name='uq_navdaily_port_date'),
    )

    portfolio = relationship("Portfolio", back_populates="navs_daily")

# AssetClassReturnDaily 테이블 모델
class AssetClassReturnDaily(Base):
    """자산군별 일일 수익률 저장 테이블
    - TWR 방식으로 계산된 일일 수익률
    - 전일 자산군 가중치 × 당일 개별자산 수익률의 합
    - 수익률은 DECIMAL(10,6)으로 저장 (±9999.999999 범위)
    """
    __tablename__ = 'asset_class_returns_daily'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    date = Column(Date, nullable=False)
    asset_class = Column(Enum(*ASSET_CLASS_ENUM, name='asset_class_enum'), nullable=False)
    daily_return = Column(Numeric(10, 6), nullable=False)
    
    # 관계 설정
    portfolio = relationship("Portfolio")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'date', 'asset_class',
                        name='uq_assetclass_ret_port_date_class'),
    )

# 기간별 자산 기여도 테이블 모델
class AssetAttributionPeriodic(Base):
    """기간별 자산 단위 기여도 분석 결과"""
    __tablename__ = 'asset_attribution_periodic'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete="CASCADE"), nullable=False)
    period_type = Column(Enum(*PERIOD_TYPE_ENUM, name='period_type_enum'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    asset_id = Column(Integer, ForeignKey('assets.id', ondelete="CASCADE"), nullable=False)
    
    start_nav = Column(Numeric(20,4), nullable=False)
    end_nav = Column(Numeric(20,4), nullable=False)
    avg_weight = Column(Numeric(10,6), nullable=False)
    total_return = Column(Numeric(10,6), nullable=False)
    contribution = Column(Numeric(10,6), nullable=False)
    selection_effect = Column(Numeric(10,6))
    allocation_effect = Column(Numeric(10,6))
    
    # 관계 설정
    portfolio = relationship("Portfolio", back_populates="asset_attributions")
    asset = relationship("Asset")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'period_type', 'start_date', 'end_date', 'asset_id',
                        name='uq_attribution_period'),
    )

# 기간별 자산군 기여도 테이블 모델
class AssetClassAttributionPeriodic(Base):
    """기간별 자산군 단위 기여도 분석 결과"""
    __tablename__ = 'asset_class_attribution_periodic'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete="CASCADE"), nullable=False)
    period_type = Column(Enum(*PERIOD_TYPE_ENUM, name='period_type_enum'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    asset_class = Column(Enum(*ASSET_CLASS_ENUM, name='asset_class_enum'), nullable=False)
    
    start_nav = Column(Numeric(20,4), nullable=False)
    end_nav = Column(Numeric(20,4), nullable=False)
    avg_weight = Column(Numeric(10,6), nullable=False)
    total_return = Column(Numeric(10,6), nullable=False)
    contribution = Column(Numeric(10,6), nullable=False)
    selection_effect = Column(Numeric(10,6))
    allocation_effect = Column(Numeric(10,6))
    risk_contribution = Column(Numeric(10,6))
    tracking_error_contrib = Column(Numeric(10,6))
    
    # 관계 설정
    portfolio = relationship("Portfolio", back_populates="class_attributions")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'period_type', 'start_date', 'end_date', 'asset_class',
                        name='uq_class_attribution_period'),
    )

# Top/Bottom 기여자 테이블 모델
class AttributionHighlightsPeriodic(Base):
    """기간별 Top/Bottom 기여자 분석 결과"""
    __tablename__ = 'attribution_highlights_periodic'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete="CASCADE"), nullable=False)
    period_type = Column(Enum(*PERIOD_TYPE_ENUM, name='period_type_enum'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rank_type = Column(Enum(*RANK_TYPE_ENUM, name='rank_type_enum'), nullable=False)
    rank_number = Column(Integer, nullable=False)
    asset_id = Column(Integer, ForeignKey('assets.id', ondelete="CASCADE"), nullable=False)
    
    contribution = Column(Numeric(10,6), nullable=False)
    weight_avg = Column(Numeric(10,6), nullable=False)
    return_total = Column(Numeric(10,6), nullable=False)
    
    # 관계 설정
    portfolio = relationship("Portfolio", back_populates="attribution_highlights")
    asset = relationship("Asset")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'period_type', 'start_date', 'end_date', 
                        'rank_type', 'rank_number',
                        name='uq_highlights_period'),
    )

"""데이터베이스 연결 설정
민감정보는 환경변수(.env)로 분리합니다.
다음 두 가지 방식 중 하나를 사용하세요.
1) DATABASE_URL 전체 문자열 제공
2) DB_DIALECT/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME 개별 제공
"""

# 우선 순위 1: DATABASE_URL이 직접 지정된 경우 사용
DATABASE_URL = os.getenv("DATABASE_URL")

# 우선 순위 2: 개별 설정으로 구성
if not DATABASE_URL:
    DB_DIALECT = os.getenv("DB_DIALECT", "mysql+pymysql")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT")  # 없으면 기본 포트 사용
    DB_NAME = os.getenv("DB_NAME", "portfolio_manager")

    host_part = f"{DB_HOST}:{DB_PORT}" if DB_PORT else DB_HOST
    DATABASE_URL = f"{DB_DIALECT}://{DB_USER}:{DB_PASSWORD}@{host_part}/{DB_NAME}"

# SQLAlchemy 로그 출력 제어 (기본 False)
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO)

# 세션 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Portfolio Analytics 관련 추가 테이블들
class PortfolioPerformance(Base):
    __tablename__ = 'portfolio_performance'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    date = Column(Date, nullable=False)
    portfolio_value = Column(Numeric(15, 2), nullable=False)
    benchmark_value = Column(Numeric(15, 2), nullable=False)
    daily_return = Column(Numeric(8, 4))
    monthly_return = Column(Numeric(8, 4))
    quarterly_return = Column(Numeric(8, 4))
    
    # Relationship
    portfolio = relationship("Portfolio", back_populates="performance_data")
    
    __table_args__ = (UniqueConstraint('portfolio_id', 'date', name='unique_portfolio_date'),)

class PortfolioAttribution(Base):
    __tablename__ = 'portfolio_attribution'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    asset_class = Column(String(50), nullable=False)
    allocation = Column(Numeric(6, 3), nullable=False)
    contribution = Column(Numeric(8, 4), nullable=False)
    date = Column(Date, nullable=False)
    
    # Relationship
    portfolio = relationship("Portfolio")

class PortfolioRiskMetrics(Base):
    __tablename__ = 'portfolio_risk_metrics'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    date = Column(Date, nullable=False)
    var_95 = Column(Numeric(8, 4), nullable=False)
    var_99 = Column(Numeric(8, 4), nullable=False)
    expected_shortfall = Column(Numeric(8, 4), nullable=False)
    tracking_error = Column(Numeric(6, 3), nullable=False)
    information_ratio = Column(Numeric(6, 3), nullable=False)
    sharpe_ratio = Column(Numeric(6, 3), nullable=False)
    volatility = Column(Numeric(6, 3), nullable=False)
    max_drawdown = Column(Numeric(6, 3), nullable=False)
    beta = Column(Numeric(6, 3), nullable=False)
    
    # Relationship
    portfolio = relationship("Portfolio")

class PortfolioSectorAllocation(Base):
    __tablename__ = 'portfolio_sector_allocation'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    sector = Column(String(100), nullable=False)
    allocation = Column(Numeric(6, 3), nullable=False)
    contribution = Column(Numeric(8, 4), nullable=False)
    date = Column(Date, nullable=False)
    
    # Relationship
    portfolio = relationship("Portfolio")

# Portfolio 모델에 relationship 추가
# (기존 Portfolio 클래스에 추가할 relationship)
# performance_data = relationship("PortfolioPerformance", back_populates="portfolio")

# 테이블 생성 (없을 경우)
Base.metadata.create_all(bind=engine)

import os
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey, UniqueConstraint, Numeric, Text, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

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
ASSET_CLASS_ENUM = (
    'SP50', 'FXCOM', 'GL_INDEX', 'GL_SECTOR', 'KR_INDEX', 'KR_SECTOR', 'MONEY_ULTRA_SHORT', 'GL_BOND_CORP', 'GL_BOND_AGG', 'KR_BOND_CORP', 'KR_BOND_AGG'
    )

# 시장 데이터용 상수 정의 (ENUM 대신 사용)
MARKET_TYPES = {
    'STOCK_INDEX': '주식 지수',
    'BOND_INDEX': '채권 지수', 
    'COMMODITY': '원자재',
    'CURRENCY': '환율',
    'RATE': '금리'
}

COUNTRIES = {
    'US': '미국',
    'KR': '한국',
    'GLOBAL': '글로벌'
}

RATE_TYPES = {
    'CENTRAL_BANK_RATE': '중앙은행 기준금리',
    'TREASURY_RATE': '국채금리',
    'CORPORATE_BOND_RATE': '회사채 금리'
}


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


class MarketInstrument(Base):
    """시장 상품 마스터 테이블 (정규화) - ENUM 없는 버전"""
    __tablename__ = 'market_instruments'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False)  # ^GSPC, USDKRW=X
    name = Column(String(100), nullable=False)  # S&P 500, USD/KRW
    market_type = Column(String(20), nullable=False)  # STOCK_INDEX, CURRENCY, RATE 등
    country = Column(String(10), nullable=False)  # US, KR, GLOBAL 등
    currency = Column(String(3), nullable=False)  # USD, KRW
    description = Column(String(200))
    is_active = Column(String(10), default='Yes')
    
    # 관계 설정
    price_data = relationship("MarketPriceDaily", back_populates="instrument", cascade="all, delete-orphan")
    rate_data = relationship("RiskFreeRateDaily", back_populates="instrument", cascade="all, delete-orphan")


class MarketPriceDaily(Base):
    """통합 시장 가격 데이터 테이블"""
    __tablename__ = 'market_price_daily'
    
    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey('market_instruments.id'), nullable=False)
    date = Column(Date, nullable=False)
    
    # 가격 데이터 (모든 타입에 공통)
    open_price = Column(Numeric(20, 8))
    high_price = Column(Numeric(20, 8))
    low_price = Column(Numeric(20, 8))
    close_price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 0))
    
    # 계산된 필드
    daily_return = Column(Numeric(10, 6))  # %
    
    # 관계 설정
    instrument = relationship("MarketInstrument", back_populates="price_data")
    
    # 제약조건
    __table_args__ = (
        UniqueConstraint('instrument_id', 'date', name='unique_instrument_date'),
    )


class RiskFreeRateDaily(Base):
    """무위험 이자율 전용 테이블 - ENUM 없는 버전"""
    __tablename__ = 'risk_free_rate_daily'
    
    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey('market_instruments.id'), nullable=False)
    date = Column(Date, nullable=False)
    rate = Column(Numeric(8, 4), nullable=False)  # 이자율 (%)
    rate_type = Column(String(30), nullable=False)  # CENTRAL_BANK_RATE, TREASURY_RATE 등
    
    # 관계 설정
    instrument = relationship("MarketInstrument", back_populates="rate_data")
    
    # 제약조건
    __table_args__ = (
        UniqueConstraint('instrument_id', 'date', name='unique_rate_instrument_date'),
    )


# =============================================================================
# 하위 호환성을 위한 뷰 클래스들
# =============================================================================

class MarketDataHelper:
    """시장 데이터 조회를 위한 헬퍼 클래스"""
    
    @staticmethod
    def validate_market_type(market_type: str) -> bool:
        """마켓 타입 유효성 검사"""
        return market_type in MARKET_TYPES
    
    @staticmethod
    def validate_country(country: str) -> bool:
        """국가 코드 유효성 검사"""
        return country in COUNTRIES
    
    @staticmethod
    def validate_rate_type(rate_type: str) -> bool:
        """금리 타입 유효성 검사"""
        return rate_type in RATE_TYPES
    
    @staticmethod
    def get_market_type_name(market_type: str) -> str:
        """마켓 타입의 한국어 이름 반환"""
        return MARKET_TYPES.get(market_type, market_type)
    
    @staticmethod
    def get_country_name(country: str) -> str:
        """국가 코드의 한국어 이름 반환"""
        return COUNTRIES.get(country, country)
    
    @staticmethod
    def get_benchmark_data(session, start_date=None, end_date=None, symbols=None):
        """벤치마크 지수 데이터 조회 (기존 BenchmarkIndex 테이블 대체)"""
        query = session.query(
            MarketPriceDaily.id,
            MarketInstrument.symbol,
            MarketInstrument.name,
            MarketInstrument.country,
            MarketPriceDaily.date,
            MarketPriceDaily.close_price,
            MarketInstrument.currency,
            MarketPriceDaily.daily_return
        ).join(MarketInstrument).filter(
            MarketInstrument.market_type == 'STOCK_INDEX',
            MarketInstrument.is_active == 'Yes'
        )
        
        if start_date:
            query = query.filter(MarketPriceDaily.date >= start_date)
        if end_date:
            query = query.filter(MarketPriceDaily.date <= end_date)
        if symbols:
            query = query.filter(MarketInstrument.symbol.in_(symbols))
            
        return query.order_by(MarketInstrument.symbol, MarketPriceDaily.date).all()
    
    @staticmethod
    def get_exchange_rate_data(session, start_date=None, end_date=None, pairs=None):
        """환율 데이터 조회 (기존 ExchangeRate 테이블 대체)"""
        query = session.query(
            MarketPriceDaily.id,
            MarketInstrument.symbol.label('currency_pair'),
            MarketPriceDaily.date,
            MarketPriceDaily.close_price.label('close_rate'),
            MarketPriceDaily.daily_return
        ).join(MarketInstrument).filter(
            MarketInstrument.market_type == 'CURRENCY',
            MarketInstrument.is_active == 'Yes'
        )
        
        if start_date:
            query = query.filter(MarketPriceDaily.date >= start_date)
        if end_date:
            query = query.filter(MarketPriceDaily.date <= end_date)
        if pairs:
            query = query.filter(MarketInstrument.symbol.in_(pairs))
            
        return query.order_by(MarketInstrument.symbol, MarketPriceDaily.date).all()
    
    @staticmethod
    def get_risk_free_rate_data(session, start_date=None, end_date=None, countries=None):
        """무위험 이자율 데이터 조회 (기존 RiskFreeRate 테이블 대체)"""
        query = session.query(
            RiskFreeRateDaily.id,
            MarketInstrument.country,
            RiskFreeRateDaily.rate_type,
            MarketInstrument.name,
            MarketInstrument.symbol,
            RiskFreeRateDaily.date,
            RiskFreeRateDaily.rate,
            MarketInstrument.currency
        ).join(MarketInstrument).filter(
            MarketInstrument.market_type == 'RATE',
            MarketInstrument.is_active == 'Yes'
        )
        
        if start_date:
            query = query.filter(RiskFreeRateDaily.date >= start_date)
        if end_date:
            query = query.filter(RiskFreeRateDaily.date <= end_date)
        if countries:
            query = query.filter(MarketInstrument.country.in_(countries))
            
        return query.order_by(MarketInstrument.country, RiskFreeRateDaily.date).all()

    @staticmethod
    def initialize_instruments(session):
        """초기 마켓 인스트루먼트 데이터 생성"""
        instruments = [
            # 미국 주식 지수
            {'symbol': '^GSPC', 'name': 'S&P 500', 'market_type': 'STOCK_INDEX', 'country': 'US', 'currency': 'USD'},
            {'symbol': '^IXIC', 'name': 'NASDAQ Composite', 'market_type': 'STOCK_INDEX', 'country': 'US', 'currency': 'USD'},
            
            # 한국 주식 지수
            {'symbol': '^KS11', 'name': 'KOSPI', 'market_type': 'STOCK_INDEX', 'country': 'KR', 'currency': 'KRW'},
            {'symbol': '^KQ11', 'name': 'KOSDAQ', 'market_type': 'STOCK_INDEX', 'country': 'KR', 'currency': 'KRW'},
            
            # 환율
            {'symbol': 'USDKRW=X', 'name': 'USD/KRW', 'market_type': 'CURRENCY', 'country': 'GLOBAL', 'currency': 'KRW'},
            
            # 무위험 이자율
            {'symbol': '^IRX', 'name': '3-Month Treasury Bill', 'market_type': 'RATE', 'country': 'US', 'currency': 'USD'},
            {'symbol': 'KOR_BASE_RATE', 'name': '한국은행 기준금리', 'market_type': 'RATE', 'country': 'KR', 'currency': 'KRW'},
        ]
        
        for instrument_data in instruments:
            existing = session.query(MarketInstrument).filter(
                MarketInstrument.symbol == instrument_data['symbol']
            ).first()
            
            if not existing:
                instrument = MarketInstrument(**instrument_data)
                session.add(instrument)
        
        session.commit()
        return len(instruments)


"""데이터베이스 연결 설정
민감정보는 환경변수(.env)로 분리합니다.
다음 두 가지 방식 중 하나를 사용하세요.
1) DATABASE_URL 전체 문자열 제공
2) DB_DIALECT/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME 개별 제공
"""

# 우선 순위 1: DATABASE_URL이 직접 지정된 경우 사용
DATABASE_URL = os.getenv("DATABASE_URL")

# # 우선 순위 2: 개별 설정으로 구성
# if not DATABASE_URL:
#     DB_DIALECT = os.getenv("DB_DIALECT", "mysql+pymysql")
#     DB_USER = os.getenv("DB_USER", "root")
#     DB_PASSWORD = os.getenv("DB_PASSWORD", "")
#     DB_HOST = os.getenv("DB_HOST", "localhost")
#     DB_PORT = os.getenv("DB_PORT")  # 없으면 기본 포트 사용
#     DB_NAME = os.getenv("DB_NAME", "portfolio_manager")

#     host_part = f"{DB_HOST}:{DB_PORT}" if DB_PORT else DB_HOST
#     DATABASE_URL = f"{DB_DIALECT}://{DB_USER}:{DB_PASSWORD}@{host_part}/{DB_NAME}"

# SQLAlchemy 로그 출력 제어 (기본 False)
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO)

# 세션 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테이블 생성 (없을 경우)
Base.metadata.create_all(bind=engine)

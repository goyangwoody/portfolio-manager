"""
Transaction and trading schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as Date, datetime
from enum import Enum

# ================================
# TRANSACTION ENUMS
# ================================

class TransactionType(str, Enum):
    """거래 유형"""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    MERGER = "merger"

class TransactionStatus(str, Enum):
    """거래 상태"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"

# ================================
# TRANSACTION SCHEMAS
# ================================

class TransactionBase(BaseModel):
    """거래 기본 정보"""
    asset_id: int
    transaction_type: TransactionType
    quantity: float = Field(description="수량")
    unit_price: float = Field(description="단가")
    transaction_date: Date = Field(description="거래일")

class TransactionCreate(TransactionBase):
    """거래 생성 요청"""
    notes: Optional[str] = Field(None, description="메모")

class TransactionUpdate(BaseModel):
    """거래 수정 요청"""
    quantity: Optional[float] = Field(None, description="수량")
    unit_price: Optional[float] = Field(None, description="단가")
    transaction_date: Optional[Date] = Field(None, description="거래일")
    notes: Optional[str] = Field(None, description="메모")

class Transaction(TransactionBase):
    """거래 정보"""
    transaction_id: int
    ticker: str = Field(description="자산 티커")
    name: str = Field(description="자산명")
    asset_class: str = Field(description="자산클래스")
    
    # 계산된 필드
    total_amount: float = Field(description="총 거래금액")
    fees: Optional[float] = Field(None, description="수수료")
    net_amount: Optional[float] = Field(None, description="순 거래금액")
    
    # 메타데이터
    status: TransactionStatus = Field(default=TransactionStatus.EXECUTED)
    created_at: datetime = Field(description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    notes: Optional[str] = Field(None, description="메모")
    
    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    """거래 조회 응답"""
    transactions: List[Transaction] = Field(description="거래 목록")
    total_count: int = Field(description="총 거래 수")
    
    # 필터 정보
    start_date: Optional[Date] = Field(None, description="조회 시작일")
    end_date: Optional[Date] = Field(None, description="조회 종료일")
    asset_id: Optional[int] = Field(None, description="필터된 자산 ID")
    transaction_type: Optional[TransactionType] = Field(None, description="필터된 거래 유형")

# ================================
# TRANSACTION SUMMARY SCHEMAS
# ================================

class TransactionSummary(BaseModel):
    """거래 요약"""
    period_start: Date = Field(description="기간 시작일")
    period_end: Date = Field(description="기간 종료일")
    
    # 거래 통계
    total_transactions: int = Field(description="총 거래 수")
    buy_transactions: int = Field(description="매수 거래 수")
    sell_transactions: int = Field(description="매도 거래 수")
    
    # 금액 통계
    total_buy_amount: float = Field(description="총 매수금액")
    total_sell_amount: float = Field(description="총 매도금액")
    net_flow: float = Field(description="순 현금흐름")
    
    # 수수료 통계
    total_fees: Optional[float] = Field(None, description="총 수수료")

class AssetTransactionSummary(BaseModel):
    """자산별 거래 요약"""
    asset_id: int
    ticker: str
    name: str
    asset_class: str
    
    # 거래 통계
    total_transactions: int = Field(description="거래 수")
    total_quantity_bought: float = Field(description="총 매수 수량")
    total_quantity_sold: float = Field(description="총 매도 수량")
    net_quantity: float = Field(description="순 수량")
    
    # 금액 통계
    total_amount_bought: float = Field(description="총 매수금액")
    total_amount_sold: float = Field(description="총 매도금액")
    net_amount: float = Field(description="순 금액")
    
    # 평균 단가
    avg_buy_price: Optional[float] = Field(None, description="평균 매수단가")
    avg_sell_price: Optional[float] = Field(None, description="평균 매도단가")
    
    class Config:
        from_attributes = True

class TransactionSummaryResponse(BaseModel):
    """거래 요약 응답"""
    overall_summary: TransactionSummary = Field(description="전체 거래 요약")
    asset_summaries: List[AssetTransactionSummary] = Field(description="자산별 거래 요약")
    
    # 기간 정보
    start_date: Date = Field(description="조회 시작일")
    end_date: Date = Field(description="조회 종료일")

# ================================
# BULK TRANSACTION SCHEMAS
# ================================

class BulkTransactionCreate(BaseModel):
    """대량 거래 생성 요청"""
    transactions: List[TransactionCreate] = Field(description="거래 목록")

class BulkTransactionResponse(BaseModel):
    """대량 거래 생성 응답"""
    successful_transactions: List[Transaction] = Field(description="성공한 거래 목록")
    failed_transactions: List[dict] = Field(description="실패한 거래 목록 (오류 정보 포함)")
    
    # 결과 요약
    total_requested: int = Field(description="요청된 거래 수")
    successful_count: int = Field(description="성공한 거래 수")
    failed_count: int = Field(description="실패한 거래 수")

# ================================
# CASH FLOW SCHEMAS
# ================================

class CashFlow(BaseModel):
    """현금흐름"""
    date: Date = Field(description="날짜")
    inflow: float = Field(description="유입 (매도, 배당 등)")
    outflow: float = Field(description="유출 (매수)")
    net_flow: float = Field(description="순 현금흐름")

class CashFlowResponse(BaseModel):
    """현금흐름 응답"""
    cash_flows: List[CashFlow] = Field(description="현금흐름 목록")
    
    # 기간 요약
    total_inflow: float = Field(description="총 유입")
    total_outflow: float = Field(description="총 유출")
    net_cash_flow: float = Field(description="순 현금흐름")
    
    # 기간 정보
    start_date: Date = Field(description="조회 시작일")
    end_date: Date = Field(description="조회 종료일")

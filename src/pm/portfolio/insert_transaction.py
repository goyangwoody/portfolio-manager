from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pm.db.models import SessionLocal, Transaction

# 8자리 소수 정밀도 (Numeric(20,8) 대응)
_SCALE = Decimal("0.00000001")

def _to_dec8(x) -> Decimal:
    """
    임의 입력 x를 Decimal(소수 8자리)로 정규화.
    - 숫자/문자 모두 허용 (None 불허)
    - 쉼표가 포함된 문자열도 처리
    """
    if x is None:
        raise ValueError("값이 None 입니다. Decimal로 변환할 수 없습니다.")
    if isinstance(x, Decimal):
        return x.quantize(_SCALE, rounding=ROUND_HALF_UP)
    if isinstance(x, (int, float)):
        # float의 이진 오차를 줄이기 위해 str로 감싼 뒤 Decimal 생성
        return Decimal(str(x)).quantize(_SCALE, rounding=ROUND_HALF_UP)
    # 문자열 등
    s = str(x).strip().replace(",", "")
    try:
        return Decimal(s).quantize(_SCALE, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Decimal(20,8)로 변환 실패: {x!r}") from e

def _to_date(d):
    """date 또는 'YYYY-MM-DD' 문자열 허용."""
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        try:
            return date.fromisoformat(d)
        except ValueError:
            # 유연성: datetime 형태 문자열일 수도 있으니 한 번 더 시도
            return datetime.fromisoformat(d).date()
    raise ValueError(f"날짜 형식이 올바르지 않습니다: {d!r}")

def add_transaction(portfolio_id, asset_id, trans_date, quantity, price, fee, tax, type_):
    """
    모든 숫자 인자(quantity, price, fee, tax)를 Decimal(20,8)로 정규화 후 저장.
    trans_date는 date 또는 'YYYY-MM-DD' 문자열 허용.
    """
    session = SessionLocal()
    try:
        tx = Transaction(
            portfolio_id = int(portfolio_id),
            asset_id     = int(asset_id),
            trans_date   = _to_date(trans_date),
            quantity     = _to_dec8(quantity),
            price        = _to_dec8(price),
            fee          = _to_dec8(fee),
            tax          = _to_dec8(tax),
            type         = type_,
        )
        session.add(tx)
        session.commit()
        print(f"거래 입력 완료: {tx.id}")
        return tx.id
    except Exception as e:
        session.rollback()
        print("거래 입력 실패:", e)
        raise
    finally:
        session.close()

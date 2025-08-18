# src/db/init_portfolios.py

from datetime import date
from pm.db.models import SessionLocal, Portfolio

def init_portfolios():
    session = SessionLocal()
    try:
        # 이미 같은 이름의 포트폴리오가 있으면 스킵할 수도 있고, 
        # 이 예시는 무조건 추가하는 방식입니다.
        p1 = Portfolio(name='USDCore',      created_at=date.today())
        p2 = Portfolio(name='USDSatellite', created_at=date.today())

        session.add_all([p1, p2])
        session.commit()
        print(f"✅ 추가된 포트폴리오: {p1.id}({p1.name}), {p2.id}({p2.name})")
    except Exception as e:
        session.rollback()
        print("❌ 포트폴리오 초기화 실패:", e)
    finally:
        session.close()

if __name__ == "__main__":
    init_portfolios()

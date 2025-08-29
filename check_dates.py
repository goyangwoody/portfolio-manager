import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.database import SessionLocal
from src.pm.db.models import PortfolioPositionDaily

def check_available_dates():
    db = SessionLocal()
    try:
        print("🔍 Checking available dates in PortfolioPositionDaily...")
        
        # 포트폴리오별 최신/최초 날짜 확인
        from sqlalchemy import func, distinct
        
        result = db.query(
            PortfolioPositionDaily.portfolio_id,
            func.min(PortfolioPositionDaily.as_of_date).label('earliest_date'),
            func.max(PortfolioPositionDaily.as_of_date).label('latest_date'),
            func.count(distinct(PortfolioPositionDaily.as_of_date)).label('date_count')
        ).group_by(PortfolioPositionDaily.portfolio_id).all()
        
        print(f"\n📅 Date ranges by portfolio:")
        for row in result:
            print(f"   Portfolio {row.portfolio_id}: {row.earliest_date} ~ {row.latest_date} ({row.date_count} dates)")
        
        # 전체 날짜 목록 확인 (최근 10개)
        recent_dates = db.query(
            distinct(PortfolioPositionDaily.as_of_date)
        ).order_by(PortfolioPositionDaily.as_of_date.desc()).limit(10).all()
        
        print(f"\n📊 Recent 10 dates with data:")
        for date_row in recent_dates:
            date_str = date_row[0]
            count = db.query(PortfolioPositionDaily).filter(
                PortfolioPositionDaily.as_of_date == date_str
            ).count()
            print(f"   {date_str}: {count} records")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_available_dates()

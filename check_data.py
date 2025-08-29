import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.database import SessionLocal
from sqlalchemy import text

def check_portfolio_position_daily():
    db = SessionLocal()
    try:
        # 테이블 존재 확인
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='portfolio_positions_daily'"))
        table_exists = result.fetchone()
        
        if not table_exists:
            print("❌ portfolio_positions_daily 테이블이 존재하지 않습니다!")
            
            # 모든 테이블 목록 출력
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print("Available tables:", tables)
            return
        
        print("✅ portfolio_positions_daily 테이블이 존재합니다")
        
        # 레코드 수 확인
        result = db.execute(text('SELECT COUNT(*) FROM portfolio_positions_daily'))
        count = result.scalar()
        print(f"📊 Total records: {count}")
        
        if count == 0:
            print("⚠️ 테이블에 데이터가 없습니다!")
            return
        
        # 컬럼 정보
        result = db.execute(text("PRAGMA table_info(portfolio_positions_daily)"))
        columns = result.fetchall()
        print("\n📋 Table columns:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # 첫 번째 레코드 확인
        result = db.execute(text('SELECT * FROM portfolio_positions_daily LIMIT 1'))
        first_row = result.fetchone()
        if first_row:
            print("\n📄 First record:")
            row_dict = dict(first_row._mapping)
            for key, value in row_dict.items():
                print(f"   {key}: {value}")
        
        # 포트폴리오별 통계
        result = db.execute(text('''
            SELECT 
                portfolio_id, 
                COUNT(*) as record_count,
                MIN(as_of_date) as earliest_date,
                MAX(as_of_date) as latest_date
            FROM portfolio_positions_daily 
            GROUP BY portfolio_id
        '''))
        
        print("\n📈 Portfolio statistics:")
        for row in result.fetchall():
            print(f"   Portfolio {row[0]}: {row[1]} records ({row[2]} to {row[3]})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_portfolio_position_daily()

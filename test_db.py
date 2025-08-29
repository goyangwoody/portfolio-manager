from api.database import SessionLocal
from sqlalchemy import text

# 데이터베이스 연결
db = SessionLocal()

try:
    # 전체 레코드 수 확인
    result = db.execute(text('SELECT COUNT(*) FROM PortfolioPositionDaily'))
    total_count = result.scalar()
    print(f'Total records in PortfolioPositionDaily: {total_count}')
    
    # 컬럼 정보 확인
    result = db.execute(text("PRAGMA table_info(PortfolioPositionDaily)"))
    columns = result.fetchall()
    print('\nTable columns:')
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    
    # 샘플 데이터 확인 (dict 형태로)
    result = db.execute(text('SELECT * FROM PortfolioPositionDaily LIMIT 3'))
    print('\nSample data:')
    rows = result.fetchall()
    for i, row in enumerate(rows):
        print(f"Row {i+1}:")
        row_dict = dict(row._mapping)
        for key, value in row_dict.items():
            print(f"  {key}: {value}")
        print()
    
    # 포트폴리오별 레코드 수 확인
    result = db.execute(text('SELECT portfolio_id, COUNT(*) as count FROM PortfolioPositionDaily GROUP BY portfolio_id'))
    print('Records by portfolio:')
    for row in result.fetchall():
        print(f"  Portfolio {row[0]}: {row[1]} records")
        
except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()

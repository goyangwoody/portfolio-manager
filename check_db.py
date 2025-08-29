from api.database import get_db
from sqlalchemy import text

db = next(get_db())
# PortfolioPositionsDaily 테이블 구조 확인
result = db.execute(text('PRAGMA table_info(PortfolioPositionsDaily)')).fetchall()
print('PortfolioPositionsDaily 테이블 구조:')
for row in result:
    print(f'  {row[1]} ({row[2]})')

# 샘플 데이터 확인
sample = db.execute(text('SELECT * FROM PortfolioPositionsDaily LIMIT 5')).fetchall()
print(f'\n샘플 데이터:')
for row in sample:
    print(f'  {row}')

# 데이터 개수 확인
count = db.execute(text('SELECT COUNT(*) FROM PortfolioPositionsDaily')).fetchone()
print(f'\n총 데이터 개수: {count[0]}')mport get_db
from sqlalchemy import text

db = next(get_db())
# portfoliopositionsdaily 테이블 구조 확인
result = db.execute(text('PRAGMA table_info(portfoliopositionsdaily)')).fetchall()
print('portfoliopositionsdaily 테이블 구조:')
for row in result:
    print(f'  {row[1]} ({row[2]})')

# 샘플 데이터 확인
sample = db.execute(text('SELECT * FROM portfoliopositionsdaily LIMIT 5')).fetchall()
print(f'\n샘플 데이터:')
for row in sample:
    print(f'  {row}')

# 데이터 개수 확인
count = db.execute(text('SELECT COUNT(*) FROM portfoliopositionsdaily')).fetchone()
print(f'\n총 데이터 개수: {count[0]}')

db.close()

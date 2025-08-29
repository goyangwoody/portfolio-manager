import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.database import SessionLocal
from src.pm.db.models import PortfolioPositionDaily, Asset, Price

def test_models_and_db():
    print("🔍 Testing database connection and models...")
    
    db = SessionLocal()
    try:
        # 모델들이 제대로 import되었는지 확인
        print(f"✅ Models imported successfully:")
        print(f"   PortfolioPositionDaily: {PortfolioPositionDaily}")
        print(f"   Asset: {Asset}")
        print(f"   Price: {Price}")
        
        # 간단한 쿼리 테스트
        print("\n🔍 Testing simple queries...")
        
        # 포트폴리오 포지션 카운트
        ppd_count = db.query(PortfolioPositionDaily).count()
        print(f"   PortfolioPositionDaily records: {ppd_count}")
        
        # 자산 카운트
        asset_count = db.query(Asset).count()
        print(f"   Asset records: {asset_count}")
        
        # 가격 카운트
        price_count = db.query(Price).count()
        print(f"   Price records: {price_count}")
        
        if ppd_count > 0:
            # 첫 번째 포지션 레코드
            first_position = db.query(PortfolioPositionDaily).first()
            print(f"\n📄 First position record:")
            print(f"   Portfolio ID: {first_position.portfolio_id}")
            print(f"   Date: {first_position.as_of_date}")
            print(f"   Asset ID: {first_position.asset_id}")
            print(f"   Quantity: {first_position.quantity}")
            
            # Join 테스트
            print(f"\n🔗 Testing join query...")
            join_result = (
                db.query(PortfolioPositionDaily, Asset)
                .join(Asset, PortfolioPositionDaily.asset_id == Asset.id)
                .first()
            )
            
            if join_result:
                position, asset = join_result
                print(f"   ✅ Join successful: {asset.name} ({asset.ticker})")
            else:
                print(f"   ❌ Join failed - no matching records")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_models_and_db()

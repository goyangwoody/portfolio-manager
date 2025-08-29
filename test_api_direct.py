import requests
import json

def test_position_apis():
    base_url = "http://localhost:8000"
    
    try:
        print("🔍 Testing Position APIs...")
        
        # 1. 포트폴리오 목록 조회
        print("\n1. Getting portfolios...")
        portfolios_response = requests.get(f"{base_url}/api/portfolios")
        print(f"   Status: {portfolios_response.status_code}")
        
        if portfolios_response.status_code != 200:
            print(f"   Error: {portfolios_response.text}")
            return
        
        portfolios = portfolios_response.json()
        print(f"   Found {len(portfolios)} portfolios")
        
        if not portfolios:
            print("   ❌ No portfolios found!")
            return
        
        # 첫 번째 포트폴리오로 테스트
        portfolio_id = portfolios[0]['id']
        portfolio_name = portfolios[0]['name']
        print(f"   Testing with Portfolio {portfolio_id}: {portfolio_name}")
        
        # 2. 최신 포지션 조회
        print(f"\n2. Testing latest positions API...")
        latest_url = f"{base_url}/api/portfolios/{portfolio_id}/positions/latest"
        print(f"   URL: {latest_url}")
        
        latest_response = requests.get(latest_url)
        print(f"   Status: {latest_response.status_code}")
        
        if latest_response.status_code == 200:
            latest_data = latest_response.json()
            print(f"   ✅ Success! Response structure:")
            print(f"      as_of_date: {latest_data.get('as_of_date', 'N/A')}")
            print(f"      total_market_value: {latest_data.get('total_market_value', 'N/A')}")
            print(f"      asset_count: {latest_data.get('asset_count', 'N/A')}")
            
            positions = latest_data.get('positions', [])
            print(f"      positions array length: {len(positions)}")
            
            if positions:
                first_asset = positions[0]
                print(f"      First asset sample:")
                print(f"         asset_name: {first_asset.get('asset_name', 'N/A')}")
                print(f"         asset_symbol: {first_asset.get('asset_symbol', 'N/A')}")
                print(f"         quantity: {first_asset.get('quantity', 'N/A')}")
                print(f"         market_value: {first_asset.get('market_value', 'N/A')}")
            else:
                print("      ⚠️ No positions in response!")
                
        else:
            print(f"   ❌ Error: {latest_response.status_code}")
            print(f"   Response: {latest_response.text}")
        
        # 3. 특정 날짜 포지션 조회
        print(f"\n3. Testing date-specific positions API...")
        date_url = f"{base_url}/api/portfolios/{portfolio_id}/positions/2025-08-30"
        print(f"   URL: {date_url}")
        
        date_response = requests.get(date_url)
        print(f"   Status: {date_response.status_code}")
        
        if date_response.status_code == 200:
            date_data = date_response.json()
            print(f"   ✅ Success! Response structure:")
            print(f"      as_of_date: {date_data.get('as_of_date', 'N/A')}")
            print(f"      asset_count: {date_data.get('asset_count', 'N/A')}")
            
            positions = date_data.get('positions', [])
            print(f"      positions array length: {len(positions)}")
        else:
            print(f"   ❌ Error: {date_response.status_code}")
            print(f"   Response: {date_response.text}")
        
        # 4. FastAPI 문서 확인
        print(f"\n4. Testing API docs...")
        docs_response = requests.get(f"{base_url}/docs")
        print(f"   Docs Status: {docs_response.status_code}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_position_apis()

import requests
import json

def test_position_api():
    base_url = "http://localhost:8000"
    
    try:
        # 1. 포트폴리오 목록 조회
        print("1. Fetching portfolios...")
        portfolios_response = requests.get(f"{base_url}/api/portfolios")
        print(f"   Status: {portfolios_response.status_code}")
        
        if portfolios_response.status_code != 200:
            print(f"   Error: {portfolios_response.text}")
            return
            
        portfolios = portfolios_response.json()
        print(f"   Found {len(portfolios)} portfolios")
        
        if not portfolios:
            print("   No portfolios found!")
            return
            
        # 첫 번째 포트폴리오로 테스트
        portfolio_id = portfolios[0]['id']
        portfolio_name = portfolios[0]['name']
        print(f"   Testing with Portfolio {portfolio_id}: {portfolio_name}")
        
        # 2. 최신 포지션 조회
        print(f"\n2. Fetching latest positions for portfolio {portfolio_id}...")
        latest_url = f"{base_url}/api/portfolios/{portfolio_id}/positions/latest"
        print(f"   URL: {latest_url}")
        
        latest_response = requests.get(latest_url)
        print(f"   Status: {latest_response.status_code}")
        
        if latest_response.status_code == 200:
            latest_data = latest_response.json()
            print(f"   Success! Date: {latest_data.get('date', 'N/A')}")
            print(f"   Assets count: {len(latest_data.get('positions', []))}")
            
            # 첫 번째 자산 정보 출력
            positions = latest_data.get('positions', [])
            if positions:
                first_asset = positions[0]
                print(f"   First asset: {first_asset.get('asset_name', 'N/A')}")
                print(f"   Market value: {first_asset.get('market_value', 'N/A')}")
        else:
            print(f"   Error: {latest_response.text}")
            
        # 3. 특정 날짜 포지션 조회
        print(f"\n3. Fetching positions for date 2025-08-30...")
        date_url = f"{base_url}/api/portfolios/{portfolio_id}/positions/2025-08-30"
        print(f"   URL: {date_url}")
        
        date_response = requests.get(date_url)
        print(f"   Status: {date_response.status_code}")
        
        if date_response.status_code == 200:
            date_data = date_response.json()
            print(f"   Success! Date: {date_data.get('date', 'N/A')}")
            print(f"   Assets count: {len(date_data.get('positions', []))}")
        else:
            print(f"   Error: {date_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_position_api()

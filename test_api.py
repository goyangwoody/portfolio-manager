import requests
import json

# API 테스트
try:
    # 포트폴리오 목록 조회
    portfolios_response = requests.get('http://localhost:8000/api/portfolios')
    print(f"Portfolios API Status: {portfolios_response.status_code}")
    if portfolios_response.status_code == 200:
        portfolios = portfolios_response.json()
        print(f"Found {len(portfolios)} portfolios")
        
        if portfolios:
            # 첫 번째 포트폴리오로 포지션 조회
            portfolio_id = portfolios[0]['id']
            print(f"Testing with portfolio ID: {portfolio_id}")
            
            # 최신 포지션 조회
            latest_response = requests.get(f'http://localhost:8000/api/portfolios/{portfolio_id}/positions/latest')
            print(f"Latest positions API Status: {latest_response.status_code}")
            print(f"Latest positions Response: {latest_response.text[:500]}")
            
            # 특정 날짜 포지션 조회
            date_response = requests.get(f'http://localhost:8000/api/portfolios/{portfolio_id}/positions/2025-08-30')
            print(f"Date positions API Status: {date_response.status_code}")
            print(f"Date positions Response: {date_response.text[:500]}")
    
except Exception as e:
    print(f"Error: {e}")

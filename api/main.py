"""
PortfolioPulse API - Main application entry point
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가 (api/ 디렉토리에서 상위로)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import attribution, performance, portfolio, assets, position, asset, risk

# FastAPI 앱 생성
app = FastAPI(
    title="PortfolioPulse API",
    version="3.0.0",
    description="Mobile-first portfolio management API for external reporting",
    root_path="/api",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(portfolio.router)
app.include_router(attribution.router)
app.include_router(performance.router)
app.include_router(assets.router)
app.include_router(position.router)
app.include_router(asset.router)
app.include_router(risk.router)

# 헬스 체크
@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "message": "PortfolioPulse API v3.0 is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

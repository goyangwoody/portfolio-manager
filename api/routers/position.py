from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services.position import PositionService
from schemas.position import (
    PortfolioPositionsHistoryResponse,
    PortfolioPositionsByDate,
    BaseResponse
)

router = APIRouter(prefix="/portfolios", tags=["positions"])


@router.get("/{portfolio_id}/positions/latest-date")
async def get_latest_position_date(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    포트폴리오의 가장 최근 포지션 날짜 조회
    
    - **portfolio_id**: 조회할 포트폴리오 ID
    
    Returns:
        가장 최근 포지션 데이터가 있는 날짜
    """
    try:
        position_service = PositionService(db)
        latest_date = position_service.get_latest_position_date(portfolio_id)
        
        if not latest_date:
            raise HTTPException(
                status_code=404,
                detail=f"Portfolio {portfolio_id}에 대한 포지션 데이터를 찾을 수 없습니다."
            )
        
        return {"latest_date": latest_date.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/positions/history", response_model=PortfolioPositionsHistoryResponse)
async def get_portfolio_positions_history(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    limit: int = Query(30, ge=1, le=365, description="최대 조회 날짜 수"),
    db: Session = Depends(get_db)
):
    """
    포트폴리오의 일별 포지션 히스토리 조회
    
    - **portfolio_id**: 조회할 포트폴리오 ID
    - **start_date**: 시작 날짜 (선택사항, 기본값: 30일 전)
    - **end_date**: 종료 날짜 (선택사항, 기본값: 오늘)
    - **limit**: 최대 조회 날짜 수 (1-365일)
    
    Returns:
        날짜별로 그룹화된 포트폴리오 포지션 목록
    """
    try:
        position_service = PositionService(db)
        result = position_service.get_portfolio_positions_history(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/positions/latest", response_model=PortfolioPositionsByDate)
async def get_latest_portfolio_positions(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    포트폴리오의 최신 포지션 조회
    
    - **portfolio_id**: 조회할 포트폴리오 ID
    
    Returns:
        최신 날짜의 포트폴리오 포지션
    """
    print(f"🔍 Getting latest positions for portfolio {portfolio_id}")
    try:
        position_service = PositionService(db)
        result = position_service.get_latest_portfolio_positions(portfolio_id)
        
        if not result:
            print(f"❌ No position data found for portfolio {portfolio_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"Portfolio {portfolio_id}에 대한 포지션 데이터를 찾을 수 없습니다."
            )
        
        print(f"✅ Found {len(result.positions)} positions for portfolio {portfolio_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting positions for portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/positions/{as_of_date}", response_model=PortfolioPositionsByDate)
async def get_portfolio_positions_by_date(
    portfolio_id: int,
    as_of_date: date,
    db: Session = Depends(get_db)
):
    """
    특정 날짜의 포트폴리오 포지션 조회
    
    - **portfolio_id**: 조회할 포트폴리오 ID
    - **as_of_date**: 기준 날짜 (YYYY-MM-DD)
    
    Returns:
        해당 날짜의 포트폴리오 포지션
    """
    print(f"🔍 Getting positions for portfolio {portfolio_id} on {as_of_date}")
    try:
        position_service = PositionService(db)
        positions = position_service.get_portfolio_positions_by_date_range(
            portfolio_id=portfolio_id,
            start_date=as_of_date,
            end_date=as_of_date,
            limit=1
        )
        
        if not positions:
            print(f"❌ No position data found for portfolio {portfolio_id} on {as_of_date}")
            raise HTTPException(
                status_code=404,
                detail=f"Portfolio {portfolio_id}의 {as_of_date} 날짜 포지션 데이터를 찾을 수 없습니다."
            )
        
        result = positions[0]
        print(f"✅ Found {len(result.positions)} positions for portfolio {portfolio_id} on {as_of_date}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting positions for portfolio {portfolio_id} on {as_of_date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

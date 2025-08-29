"""
Common utility functions
"""
from typing import Optional
from decimal import Decimal
from datetime import date, timedelta
import re

def safe_float(value) -> Optional[float]:
    """안전하게 float로 변환"""
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def parse_custom_period(custom_week: Optional[str], custom_month: Optional[str]) -> tuple[date, date, str]:
    """
    커스텀 기간 문자열을 파싱해서 시작일/종료일 반환
    
    Args:
        custom_week: "2024-W01" 형식의 주차 문자열
        custom_month: "2024-01" 형식의 월 문자열
    
    Returns:
        tuple: (start_date, end_date, period_type)
    """
    from datetime import datetime, timedelta
    
    if custom_week:
        # 주차 파싱: "2024-W01" -> 2024년 1주차 (ISO 8601 표준)
        match = re.match(r"(\d{4})-W(\d{2})", custom_week)
        if match:
            year, week = int(match.group(1)), int(match.group(2))
            
            # Python 표준 라이브러리를 사용한 간단한 방법
            # 해당 연도의 첫 번째 목요일 찾기 (ISO 8601 기준)
            jan4 = datetime(year, 1, 4).date()  # 1월 4일은 항상 첫 번째 주에 포함
            
            # 1월 4일이 포함된 주의 월요일 찾기
            days_since_monday = jan4.weekday()  # 0=Monday, 6=Sunday
            first_week_monday = jan4 - timedelta(days=days_since_monday)
            
            # 지정된 주의 월요일과 일요일 계산
            week_start = first_week_monday + timedelta(weeks=week-1)
            week_end = week_start + timedelta(days=6)
            
            return week_start, week_end, "week"
    
    if custom_month:
        # 월 파싱: "2024-01" -> 2024년 1월
        match = re.match(r"(\d{4})-(\d{2})", custom_month)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            
            # 해당 월의 첫째 날
            month_start = date(year, month, 1)
            
            # 해당 월의 마지막 날
            if month == 12:
                next_month_start = date(year + 1, 1, 1)
            else:
                next_month_start = date(year, month + 1, 1)
            month_end = next_month_start - timedelta(days=1)
            
            return month_start, month_end, "month"
    
    # 기본값: 현재 월
    today = date.today()
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)
    month_end = next_month_start - timedelta(days=1)
    
    return month_start, month_end, "month"

def get_benchmark_value(date: date, benchmark_index: str = "SP500") -> Optional[float]:
    """
    특정 날짜의 벤치마크 지수 값을 가져옴
    
    Args:
        date: 조회할 날짜
        benchmark_index: 벤치마크 지수 종류 ("SP500", "KOSPI", "NASDAQ" 등)
    
    Returns:
        해당 날짜의 벤치마크 지수 값 (None if not found)
    """
    # TODO: 실제 벤치마크 데이터베이스나 API에서 데이터 조회
    # 예시: 외부 API (Yahoo Finance, Alpha Vantage 등) 또는 내부 DB 테이블
    pass

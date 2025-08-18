from datetime import datetime, date, timedelta
import pandas as pd
from pandas.tseries.offsets import BDay
import pandas_market_calendars as mcal

class TradingCalendar_KRX:
    """한국 거래소(KRX) 거래일 관리 클래스"""
    
    def __init__(self):
        self.krx = mcal.get_calendar('XKRX')
    
    def get_trading_dates(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 거래일 목록 반환"""
        schedule = self.krx.schedule(start_date=start_date, end_date=end_date)
        return [d.date() for d in schedule.index]
    
    def is_trading_day(self, check_date: date) -> bool:
        """해당 날짜가 거래일인지 확인"""
        return len(self.krx.valid_days(start_date=check_date, end_date=check_date)) > 0
    
    def get_last_trading_day(self, ref_date: date) -> date:
        """주어진 날짜 이전의 가장 최근 거래일 반환"""
        schedule = self.krx.schedule(start_date=ref_date - timedelta(days=10), 
                                   end_date=ref_date)
        if len(schedule) == 0:
            return None
        return schedule.index[-1].date()
    
    def get_next_trading_day(self, ref_date: date) -> date:
        """주어진 날짜 이후의 가장 빠른 거래일 반환"""
        schedule = self.krx.schedule(start_date=ref_date, 
                                   end_date=ref_date + timedelta(days=10))
        if len(schedule) == 0:
            return None
        return schedule.index[0].date()
    
    def get_week_bounds(self, ref_date: date) -> tuple:
        """해당 주의 첫 거래일과 마지막 거래일 반환
        
        Returns:
            tuple: (week_start_date, week_end_date)
        """
        # 월요일로 조정
        monday = ref_date - timedelta(days=ref_date.weekday())
        friday = monday + timedelta(days=4)
        
        # 실제 거래일 찾기
        week_start = self.get_next_trading_day(monday)
        week_end = self.get_last_trading_day(friday)
        
        return week_start, week_end
    
    def get_week_ranges(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 주간 범위 목록 반환
        
        Returns:
            list of tuple: [(week1_start, week1_end), (week2_start, week2_end), ...]
        """
        # 첫 주 월요일로 조정
        current = start_date - timedelta(days=start_date.weekday())
        
        ranges = []
        while current <= end_date:
            week_start, week_end = self.get_week_bounds(current)
            if week_start and week_end and week_end <= end_date:
                ranges.append((week_start, week_end))
            current += timedelta(days=7)
            
        return ranges
    
    def get_month_bounds(self, ref_date: date) -> tuple:
        """해당 월의 첫 거래일과 마지막 거래일 반환
        
        Returns:
            tuple: (month_start_date, month_end_date)
        """
        month_start = date(ref_date.year, ref_date.month, 1)
        if ref_date.month == 12:
            month_end = date(ref_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(ref_date.year, ref_date.month + 1, 1) - timedelta(days=1)
        
        # 실제 거래일 찾기
        first_trading_day = self.get_next_trading_day(month_start)
        last_trading_day = self.get_last_trading_day(month_end)
        
        return first_trading_day, last_trading_day
    
    def get_month_ranges(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 월간 범위 목록 반환
        
        Returns:
            list of tuple: [(month1_start, month1_end), (month2_start, month2_end), ...]
        """
        ranges = []
        current = date(start_date.year, start_date.month, 1)
        
        while current <= end_date:
            month_start, month_end = self.get_month_bounds(current)
            if month_start and month_end and month_end <= end_date:
                ranges.append((month_start, month_end))
            
            # 다음 달로 이동
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        
        return ranges
    
    def get_quarter_bounds(self, ref_date: date) -> tuple:
        """해당 분기의 첫 거래일과 마지막 거래일 반환
        
        Returns:
            tuple: (quarter_start_date, quarter_end_date)
        """
        quarter = (ref_date.month - 1) // 3
        quarter_start = date(ref_date.year, quarter * 3 + 1, 1)
        if quarter == 3:  # Q4
            quarter_end = date(ref_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            quarter_end = date(ref_date.year, (quarter + 1) * 3 + 1, 1) - timedelta(days=1)
        
        # 실제 거래일 찾기
        first_trading_day = self.get_next_trading_day(quarter_start)
        last_trading_day = self.get_last_trading_day(quarter_end)
        
        return first_trading_day, last_trading_day
    
    def get_quarter_ranges(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 분기 범위 목록 반환
        
        Returns:
            list of tuple: [(quarter1_start, quarter1_end), (quarter2_start, quarter2_end), ...]
        """
        ranges = []
        current = date(start_date.year, ((start_date.month - 1) // 3) * 3 + 1, 1)
        
        while current <= end_date:
            quarter_start, quarter_end = self.get_quarter_bounds(current)
            if quarter_start and quarter_end and quarter_end <= end_date:
                ranges.append((quarter_start, quarter_end))
            
            # 다음 분기로 이동
            if current.month == 10:  # Q4
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 3, 1)
        
        return ranges

class TradingCalendar_NYSE:
    """뉴욕 증권거래소(NYSE) 거래일 관리 클래스"""
    
    def __init__(self):
        self.nyse = mcal.get_calendar('XNYS')
    
    def get_trading_dates(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 거래일 목록 반환"""
        schedule = self.nyse.schedule(start_date=start_date, end_date=end_date)
        return [d.date() for d in schedule.index]
    
    def is_trading_day(self, check_date: date) -> bool:
        """해당 날짜가 거래일인지 확인"""
        return len(self.nyse.valid_days(start_date=check_date, end_date=check_date)) > 0
    
    def get_last_trading_day(self, ref_date: date) -> date:
        """주어진 날짜 이전의 가장 최근 거래일 반환"""
        schedule = self.nyse.schedule(start_date=ref_date - timedelta(days=10), 
                                   end_date=ref_date)
        if len(schedule) == 0:
            return None
        return schedule.index[-1].date()
    
    def get_next_trading_day(self, ref_date: date) -> date:
        """주어진 날짜 이후의 가장 빠른 거래일 반환"""
        schedule = self.nyse.schedule(start_date=ref_date, 
                                   end_date=ref_date + timedelta(days=10))
        if len(schedule) == 0:
            return None
        return schedule.index[0].date()
    
    def get_week_bounds(self, ref_date: date) -> tuple:
        """해당 주의 첫 거래일과 마지막 거래일 반환
        
        Returns:
            tuple: (week_start_date, week_end_date)
        """
        # 월요일로 조정
        monday = ref_date - timedelta(days=ref_date.weekday())
        friday = monday + timedelta(days=4)
        
        # 실제 거래일 찾기
        week_start = self.get_next_trading_day(monday)
        week_end = self.get_last_trading_day(friday)
        
        return week_start, week_end
    
    def get_week_ranges(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 주간 범위 목록 반환
        
        Returns:
            list of tuple: [(week1_start, week1_end), (week2_start, week2_end), ...]
        """
        # 첫 주 월요일로 조정
        current = start_date - timedelta(days=start_date.weekday())
        
        ranges = []
        while current <= end_date:
            week_start, week_end = self.get_week_bounds(current)
            if week_start and week_end and week_end <= end_date:
                ranges.append((week_start, week_end))
            current += timedelta(days=7)
            
        return ranges
    
    def get_month_bounds(self, ref_date: date) -> tuple:
        """해당 월의 첫 거래일과 마지막 거래일 반환
        
        Returns:
            tuple: (month_start_date, month_end_date)
        """
        month_start = date(ref_date.year, ref_date.month, 1)
        if ref_date.month == 12:
            month_end = date(ref_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(ref_date.year, ref_date.month + 1, 1) - timedelta(days=1)
        
        # 실제 거래일 찾기
        first_trading_day = self.get_next_trading_day(month_start)
        last_trading_day = self.get_last_trading_day(month_end)
        
        return first_trading_day, last_trading_day
    
    def get_month_ranges(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 월간 범위 목록 반환
        
        Returns:
            list of tuple: [(month1_start, month1_end), (month2_start, month2_end), ...]
        """
        ranges = []
        current = date(start_date.year, start_date.month, 1)
        
        while current <= end_date:
            month_start, month_end = self.get_month_bounds(current)
            if month_start and month_end and month_end <= end_date:
                ranges.append((month_start, month_end))
            
            # 다음 달로 이동
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        
        return ranges
    
    def get_quarter_bounds(self, ref_date: date) -> tuple:
        """해당 분기의 첫 거래일과 마지막 거래일 반환
        
        Returns:
            tuple: (quarter_start_date, quarter_end_date)
        """
        quarter = (ref_date.month - 1) // 3
        quarter_start = date(ref_date.year, quarter * 3 + 1, 1)
        if quarter == 3:  # Q4
            quarter_end = date(ref_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            quarter_end = date(ref_date.year, (quarter + 1) * 3 + 1, 1) - timedelta(days=1)
        
        # 실제 거래일 찾기
        first_trading_day = self.get_next_trading_day(quarter_start)
        last_trading_day = self.get_last_trading_day(quarter_end)
        
        return first_trading_day, last_trading_day
    
    def get_quarter_ranges(self, start_date: date, end_date: date) -> list:
        """주어진 기간의 분기 범위 목록 반환
        
        Returns:
            list of tuple: [(quarter1_start, quarter1_end), (quarter2_start, quarter2_end), ...]
        """
        ranges = []
        current = date(start_date.year, ((start_date.month - 1) // 3) * 3 + 1, 1)
        
        while current <= end_date:
            quarter_start, quarter_end = self.get_quarter_bounds(current)
            if quarter_start and quarter_end and quarter_end <= end_date:
                ranges.append((quarter_start, quarter_end))
            
            # 다음 분기로 이동
            if current.month == 10:  # Q4
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 3, 1)
        
        return ranges
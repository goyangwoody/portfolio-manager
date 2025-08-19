#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.pm.db.models import Portfolio, get_db

def list_portfolios():
    """List all portfolios in database"""
    for db in get_db():
        try:
            portfolios = db.query(Portfolio).all()
            print(f"Found {len(portfolios)} portfolios:")
            
            for portfolio in portfolios:
                print(f"  ID: {portfolio.id}")
                print(f"  Name: {portfolio.name}")
                print(f"  Currency: {portfolio.currency}")
                print(f"  Initial Cash: {portfolio.initial_cash}")
                print(f"  Cash Balance: {portfolio.cash_balance}")
                print(f"  Created: {portfolio.created_at}")
                print("  ---")
                
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    list_portfolios()

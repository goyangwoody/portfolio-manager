from pm.db.models import SessionLocal, Asset, Portfolio

"""
Script to update the `currency` field on each Asset based on its ticker pattern:
- If ticker ends with '.KS' (numeric.KS), assign 'KRW'
- Otherwise, assign 'USD'
"""

def update_asset_currency():
    session = SessionLocal()
    try:
        assets = session.query(Asset).all()
        for asset in assets:
            ticker = asset.ticker.upper()
            # KRW assets: numeric.KS pattern
            if ticker.endswith('.KS'):
                asset.currency = 'KRW'
            else:
                asset.currency = 'USD'
            session.add(asset)
        session.commit()
        print(f"✅ Updated currency for {len(assets)} assets.")
    except Exception as e:
        session.rollback()
        print(f"❌ Failed to update asset currency: {e}")
    finally:
        session.close()



def update_portfolio_currency():
    session = SessionLocal()
    try:
        portfolios = session.query(Portfolio).all()
        for pf in portfolios:
            name_upper = pf.name.strip().upper()
            if name_upper.startswith('USD'):
                pf.currency = 'USD'
            else:
                pf.currency = 'KRW'
            session.add(pf)
        session.commit()
        print(f"✅ Updated currency for {len(portfolios)} portfolios.")
    except Exception as e:
        session.rollback()
        print(f"❌ Failed to update portfolio currency: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    update_portfolio_currency()
    update_asset_currency()

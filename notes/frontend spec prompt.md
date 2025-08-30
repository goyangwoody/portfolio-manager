Here’s the updated version with your new requirements translated into English:

---

# Mobile Dashboard (External Reporting) – Key Summary

**Purpose & Audience**  
This dashboard is for external reporting—clear, simple, and mobile-friendly. It should give clients or investors a quick, trustworthy view of portfolio performance.

**Page Breakdown**  
- **Overview**: Big KPIs (return, Sharpe, NAV) + trend chart.  
- **Performance**: Daily/monthly returns, benchmark comparison.  
- **Attribution**: Contribution by asset class + top gainers/losers.  
- **Risk & Allocation**: Current allocation and risk metrics (volatility, drawdown).  
- **Assets (new)**: Asset list and detailed sheet per asset (see below).

**Design Principles**  
- Mobile-first: vertical flow, bottom navigation bar.  
- Charts: about 90% width, 250–300px tall.  
- KPI cards: big numbers, simple color cues.  
- **Top-level toggle**: Add a feature at the top to switch from domestic portfolios to foreign currency portfolios.

**Assets Page Requirements**  
- Asset list with repeating items.  
  - Left: Asset name + average cost (secondary text).  
  - Right: Daily % change (with color coding).  
- On tap: Show a detailed overlay sheet with:  
  - Held quantity  
  - Unrealized P/L  
  - Cumulative return  
  - Detailed chart (per asset)

**Data Needs**  
- JSON API with clear fields (date, KPIs, performance, attribution, allocation, assets).  
- Returns in decimals, dates in ISO format.

**Performance & Accessibility**  
- Lightweight pages, charts load per view.  
- Clear colors, dark/light mode, easy to read on phones.

---

Common Requirements

On every page (Performance, Attribution, Assets, Risk), add a UI element right below the domestic/foreign toggle to set the analysis period.

By default, show data “from the start of investment to the most recent date”, but also provide options to select a specific week or specific month.

It is important to apply a UI that is consistent across all pages while reflecting the characteristics of each page. Clearly highlight which period is currently being displayed.

Overview Page

Considering the short investment horizon, adjust the selectable periods in the chart.

Must include the entire investment period, and additionally provide quick options for recent 1 week, 2 weeks, 1 month, plus an option to select a specific week or month.

Performance Page

In the top summary section, remove the 3-month return and instead display 1D, 1W, and 1M returns.

Remove the Monthly Returns chart and replace it with a Daily Returns chart.

Display the Sharpe Ratio.

Attribution Page

In Attribution by Asset Class, when tapping each asset class, show detailed information such as:

Market value trend per asset class

Allocation weight trend

Return trend

In Top Contributors / Detractors, when clicking each asset, link to a detailed view of that asset (same format as the Assets page).

Risk Page

Remove Top Sector Exposure.

Add the Sharpe Ratio.
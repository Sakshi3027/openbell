"""
OpenBell — Data Fetcher
Fetches real stock data from Yahoo Finance for our 7 tracked stocks
"""

import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import pytz

STOCKS = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "META"]

ET = pytz.timezone("America/New_York")

def get_market_status():
    """Returns current market status."""
    now = datetime.now(ET)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    pre_market_start = now.replace(hour=4, minute=0, second=0, microsecond=0)

    is_weekend = now.weekday() >= 5

    if is_weekend:
        return "WEEKEND"
    elif now < pre_market_start:
        return "CLOSED"
    elif now < market_open:
        return "PRE-MARKET"
    elif now <= market_close:
        return "OPEN"
    else:
        return "AFTER-HOURS"

def fetch_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Fetch historical OHLCV data for a stock."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None)
        df["ticker"] = ticker
        df = df.reset_index()
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        print(f"  ✅ {ticker}: {len(df)} days of data")
        return df
    except Exception as e:
        print(f"  ❌ {ticker}: {e}")
        return pd.DataFrame()

def fetch_all_stocks():
    """Fetch data for all tracked stocks and save to data/raw."""
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    print(f"\n🔔 OpenBell Data Fetch")
    print(f"   Time: {datetime.now(ET).strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"   Market Status: {get_market_status()}")
    print(f"   Fetching {len(STOCKS)} stocks...\n")

    all_data = {}
    for ticker in STOCKS:
        df = fetch_stock_data(ticker)
        if not df.empty:
            # Save individual CSV
            df.to_csv(f"data/raw/{ticker}.csv", index=False)
            all_data[ticker] = df

    # Save combined summary
    summary = {
        "fetched_at": datetime.now(ET).isoformat(),
        "market_status": get_market_status(),
        "stocks_fetched": list(all_data.keys()),
        "total_stocks": len(all_data),
        "date_range": {
            ticker: {
                "from": str(df["date"].min()),
                "to": str(df["date"].max()),
                "days": len(df)
            }
            for ticker, df in all_data.items()
        }
    }

    with open("data/raw/fetch_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n📊 Fetch complete!")
    print(f"   Stocks: {len(all_data)}/{len(STOCKS)} successful")
    print(f"   Data saved to data/raw/")
    return all_data

if __name__ == "__main__":
    fetch_all_stocks()

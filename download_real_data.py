#!/usr/bin/env python3
"""
Download real market data using yfinance.

NOTE: Free intraday data has limits:
  - 1m:  last 7 days only
  - 15m: last 60 days
  - 1h:  last ~730 days
  - 1d:  unlimited

For full 5-year intraday data, use a paid provider:
  - Polygon.io (recommended, affordable)
  - Interactive Brokers API
  - Alpha Vantage (premium)
  - Databento

Usage:
    pip install yfinance
    python download_real_data.py                     # Download SPY daily 5yr
    python download_real_data.py --symbol AAPL       # Different symbol
    python download_real_data.py --interval 1h       # Hourly (max ~2yr)
    python download_real_data.py --interval 15m      # 15min (max 60 days)
"""

import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Download OHLCV data via yfinance")
    parser.add_argument("--symbol", default="SPY", help="Ticker symbol (default: SPY)")
    parser.add_argument("--interval", default="1d",
                        choices=["1m", "5m", "15m", "30m", "1h", "1d", "1wk"],
                        help="Bar interval (default: 1d)")
    parser.add_argument("--period", default=None,
                        help="Period like '5y', '2y', '60d', '7d' (auto-set based on interval if omitted)")
    parser.add_argument("--output-dir", default="data", help="Output directory")
    args = parser.parse_args()

    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed. Run: pip install yfinance")
        sys.exit(1)

    # Auto-set max period based on interval limits
    max_periods = {
        "1m": "7d", "5m": "60d", "15m": "60d", "30m": "60d",
        "1h": "730d", "1d": "5y", "1wk": "10y",
    }
    period = args.period or max_periods.get(args.interval, "5y")

    print(f"Downloading {args.symbol} @ {args.interval} for {period}...")

    ticker = yf.Ticker(args.symbol)
    df = ticker.history(period=period, interval=args.interval)

    if df.empty:
        print("No data returned. Check symbol and interval.")
        sys.exit(1)

    # Standardize columns
    df = df.rename(columns={
        "Datetime": "Date",
    })
    df.index.name = "Date"
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df = df.reset_index()

    os.makedirs(args.output_dir, exist_ok=True)
    filename = f"{args.symbol}_{args.interval}.csv"
    path = os.path.join(args.output_dir, filename)
    df.to_csv(path, index=False)

    print(f"Saved: {path} ({len(df):,} bars)")
    print(f"Date range: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")


if __name__ == "__main__":
    main()

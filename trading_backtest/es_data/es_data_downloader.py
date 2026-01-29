"""
ES Futures Data Downloader
==========================
Production-ready downloaders for every major data source.
Each function produces CSVs matching the schema in es_data_schema.py.

Supported sources:
  1. Polygon.io          (API key, $29/mo for full history)
  2. Interactive Brokers  (IBKR account + TWS/Gateway running)
  3. Databento            (API key, pay-per-query)
  4. yfinance             (free, daily only, limited quality)
  5. TradingView          (manual CSV export instructions)
  6. CME DataMine         (official, manual purchase)

Usage:
    python es_data_downloader.py --source polygon --api-key YOUR_KEY
    python es_data_downloader.py --source ibkr
    python es_data_downloader.py --source databento --api-key YOUR_KEY
    python es_data_downloader.py --source yfinance
"""

import os
import sys
import csv
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded")

HEADERS = [
    "timestamp", "open", "high", "low", "close",
    "volume", "vwap", "session", "session_high", "session_low",
]

# ES contract months: H=Mar, M=Jun, U=Sep, Z=Dec
CONTRACT_MONTHS = {3: "H", 6: "M", 9: "U", 12: "Z"}

# Approximate rollover dates (second Thursday before third Friday)
# In practice, use exact CME calendar
ROLLOVER_MONTHS = [3, 6, 9, 12]


def get_front_month_symbol(date: datetime) -> str:
    """
    Get the front-month ES contract symbol for a given date.

    Args:
        date: Current date

    Returns:
        Contract symbol like 'ESH2024'
    """
    month = date.month
    year = date.year

    for rm in ROLLOVER_MONTHS:
        if month <= rm:
            return f"ES{CONTRACT_MONTHS[rm]}{year}"

    # After December expiry, roll to March next year
    return f"ES{CONTRACT_MONTHS[3]}{year + 1}"


def classify_session(ts: datetime) -> str:
    """
    Classify a UTC timestamp as RTH or ETH.
    RTH = 14:30-21:00 UTC (9:30-16:00 ET, ignoring DST for simplicity)
    """
    hour = ts.hour
    minute = ts.minute

    # Approximate RTH: 13:30-20:00 UTC (EDT) or 14:30-21:00 UTC (EST)
    # Using a broad window that covers both
    if (hour == 13 and minute >= 30) or (14 <= hour <= 19) or (hour == 20 and minute == 0):
        return "RTH"
    if (hour == 14 and minute >= 30) or (15 <= hour <= 20) or (hour == 21 and minute == 0):
        return "RTH"
    return "ETH"


# ============================================================
# SOURCE 1: POLYGON.IO (RECOMMENDED)
# ============================================================

def download_polygon(api_key: str,
                     start_date: str = "2010-01-01",
                     end_date: str = "2025-01-01",
                     timeframes: List[str] = None) -> Dict[str, str]:
    """
    Download ES data from Polygon.io.

    Requirements:
        pip install polygon-api-client

    Args:
        api_key: Polygon.io API key
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframes: List of timeframes to download

    Returns:
        Dictionary of {timeframe: filepath}
    """
    try:
        from polygon import RESTClient
    except ImportError:
        print("Install polygon: pip install polygon-api-client")
        sys.exit(1)

    client = RESTClient(api_key=api_key)

    timeframes = timeframes or ["1min", "5min", "15min", "1hour", "daily"]

    # Polygon multiplier/timespan mapping
    tf_map = {
        "1min":  (1, "minute"),
        "5min":  (5, "minute"),
        "15min": (15, "minute"),
        "1hour": (1, "hour"),
        "daily": (1, "day"),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    paths = {}

    for tf in timeframes:
        if tf not in tf_map:
            print(f"Unknown timeframe: {tf}")
            continue

        multiplier, timespan = tf_map[tf]
        filename = f"ES_{tf}_{start_date.replace('-','')}_{end_date.replace('-','')}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)

        print(f"\nDownloading {tf} data from Polygon...")

        all_bars = []

        # Polygon uses ticker format: ES for continuous, or specific contracts
        # For continuous front-month, use "ES" with adjusted=true
        # Or iterate contracts. Using index futures ticker:
        ticker = "ES=F"  # Continuous front-month

        try:
            bars = client.get_aggs(
                ticker=f"C:ES",  # CME ES futures
                multiplier=multiplier,
                timespan=timespan,
                from_=start_date,
                to=end_date,
                adjusted=True,
                sort="asc",
                limit=50000,
            )

            for bar in bars:
                ts = datetime.fromtimestamp(bar.timestamp / 1000, tz=timezone.utc)
                session = classify_session(ts)

                all_bars.append([
                    ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    f"{bar.open:.2f}",
                    f"{bar.high:.2f}",
                    f"{bar.low:.2f}",
                    f"{bar.close:.2f}",
                    str(bar.volume),
                    f"{bar.vwap:.2f}" if bar.vwap else "",
                    session,
                    "", "",  # session_high/low computed in loader
                ])

        except Exception as e:
            print(f"Error: {e}")
            print("Trying alternative ticker formats...")

            # Alternative: use specific contract symbols
            # Iterate year by year, quarter by quarter
            current = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            while current < end:
                contract = get_front_month_symbol(current)
                quarter_end = current + timedelta(days=90)

                try:
                    bars = client.get_aggs(
                        ticker=f"C:{contract}",
                        multiplier=multiplier,
                        timespan=timespan,
                        from_=current.strftime("%Y-%m-%d"),
                        to=min(quarter_end, end).strftime("%Y-%m-%d"),
                        adjusted=True,
                        sort="asc",
                        limit=50000,
                    )

                    for bar in bars:
                        ts = datetime.fromtimestamp(bar.timestamp / 1000, tz=timezone.utc)
                        session = classify_session(ts)

                        all_bars.append([
                            ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            f"{bar.open:.2f}",
                            f"{bar.high:.2f}",
                            f"{bar.low:.2f}",
                            f"{bar.close:.2f}",
                            str(bar.volume),
                            f"{bar.vwap:.2f}" if bar.vwap else "",
                            session,
                            "", "",
                        ])

                    print(f"  {contract}: {len(bars)} bars")

                except Exception as e2:
                    print(f"  {contract}: Error - {e2}")

                current = quarter_end
                time.sleep(0.5)  # Rate limit

        # Write CSV
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)
            writer.writerows(all_bars)

        paths[tf] = filepath
        print(f"  Saved: {filepath} ({len(all_bars)} rows)")

    return paths


# ============================================================
# SOURCE 2: INTERACTIVE BROKERS
# ============================================================

def download_ibkr(timeframes: List[str] = None,
                  host: str = "127.0.0.1",
                  port: int = 7497,
                  client_id: int = 1) -> Dict[str, str]:
    """
    Download ES data from Interactive Brokers TWS/Gateway.

    Requirements:
        pip install ib_insync
        TWS or IB Gateway must be running with API connections enabled.

    Args:
        timeframes: List of timeframes
        host: TWS/Gateway host
        port: TWS/Gateway port (7497=TWS paper, 7496=TWS live, 4002=Gateway)
        client_id: API client ID

    Returns:
        Dictionary of {timeframe: filepath}
    """
    try:
        from ib_insync import IB, Future, util
    except ImportError:
        print("Install ib_insync: pip install ib_insync")
        sys.exit(1)

    timeframes = timeframes or ["1min", "5min", "15min", "1hour", "daily"]

    # IB bar size mapping
    tf_map = {
        "1min":  "1 min",
        "5min":  "5 mins",
        "15min": "15 mins",
        "1hour": "1 hour",
        "daily": "1 day",
    }

    # IB limits: 1min = 1 day, 5min = 1 week, etc.
    # We need to chunk requests
    duration_map = {
        "1min":  ("1 D", 1),        # 1 day at a time
        "5min":  ("1 W", 7),         # 1 week at a time
        "15min": ("2 W", 14),        # 2 weeks at a time
        "1hour": ("1 M", 30),        # 1 month at a time
        "daily": ("1 Y", 365),       # 1 year at a time
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    paths = {}

    ib = IB()

    try:
        ib.connect(host, port, clientId=client_id)
        print("Connected to IBKR")

        # Define ES continuous contract
        contract = Future("ES", exchange="CME")
        ib.qualifyContracts(contract)

        for tf in timeframes:
            if tf not in tf_map:
                continue

            bar_size = tf_map[tf]
            duration, step_days = duration_map[tf]

            filename = f"ES_{tf}_ibkr.csv"
            filepath = os.path.join(OUTPUT_DIR, filename)

            print(f"\nDownloading {tf} from IBKR...")

            all_bars = []
            end_dt = datetime.now()
            start_dt = datetime(2010, 1, 1)

            current_end = end_dt

            while current_end > start_dt:
                try:
                    bars = ib.reqHistoricalData(
                        contract,
                        endDateTime=current_end.strftime("%Y%m%d %H:%M:%S"),
                        durationStr=duration,
                        barSizeSetting=bar_size,
                        whatToShow="TRADES",
                        useRTH=False,  # Include ETH
                        formatDate=2,  # UTC
                    )

                    for bar in bars:
                        ts = bar.date if isinstance(bar.date, datetime) else \
                             datetime.strptime(str(bar.date), "%Y-%m-%d")
                        ts_utc = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
                        session = classify_session(ts_utc)

                        all_bars.append([
                            ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            f"{bar.open:.2f}",
                            f"{bar.high:.2f}",
                            f"{bar.low:.2f}",
                            f"{bar.close:.2f}",
                            str(int(bar.volume)),
                            f"{bar.average:.2f}" if hasattr(bar, 'average') and bar.average else "",
                            session,
                            "", "",
                        ])

                    current_end -= timedelta(days=step_days)
                    time.sleep(2)  # IB rate limit

                except Exception as e:
                    print(f"  Chunk error: {e}")
                    current_end -= timedelta(days=step_days)
                    time.sleep(10)

            # Sort by timestamp
            all_bars.sort(key=lambda x: x[0])

            # Remove duplicates
            seen = set()
            unique_bars = []
            for bar in all_bars:
                if bar[0] not in seen:
                    seen.add(bar[0])
                    unique_bars.append(bar)

            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(HEADERS)
                writer.writerows(unique_bars)

            paths[tf] = filepath
            print(f"  Saved: {filepath} ({len(unique_bars)} rows)")

    finally:
        ib.disconnect()

    return paths


# ============================================================
# SOURCE 3: DATABENTO
# ============================================================

def download_databento(api_key: str,
                       start_date: str = "2010-01-01",
                       end_date: str = "2025-01-01",
                       timeframes: List[str] = None) -> Dict[str, str]:
    """
    Download ES data from Databento.

    Requirements:
        pip install databento

    Args:
        api_key: Databento API key
        start_date: Start date
        end_date: End date
        timeframes: Timeframes to download

    Returns:
        Dictionary of {timeframe: filepath}
    """
    try:
        import databento as db
    except ImportError:
        print("Install databento: pip install databento")
        sys.exit(1)

    timeframes = timeframes or ["1min", "5min", "15min", "1hour", "daily"]

    # Databento schema mapping
    tf_map = {
        "1min":  "ohlcv-1m",
        "5min":  "ohlcv-5m",  # May need to resample from 1m
        "15min": "ohlcv-15m",  # May need to resample from 1m
        "1hour": "ohlcv-1h",
        "daily": "ohlcv-1d",
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    paths = {}

    client = db.Historical(api_key)

    for tf in timeframes:
        schema = tf_map.get(tf, "ohlcv-1m")

        filename = f"ES_{tf}_databento.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)

        print(f"\nDownloading {tf} from Databento...")

        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",  # CME Globex
                symbols=["ES.FUT"],   # ES continuous front-month
                schema=schema,
                start=start_date,
                end=end_date,
            )

            df = data.to_df()

            all_bars = []
            for idx, row in df.iterrows():
                ts = idx if isinstance(idx, datetime) else pd.Timestamp(idx)
                ts_utc = ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")
                session = classify_session(ts_utc)

                all_bars.append([
                    ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    f"{row['open']:.2f}",
                    f"{row['high']:.2f}",
                    f"{row['low']:.2f}",
                    f"{row['close']:.2f}",
                    str(int(row['volume'])),
                    "",
                    session,
                    "", "",
                ])

            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(HEADERS)
                writer.writerows(all_bars)

            paths[tf] = filepath
            print(f"  Saved: {filepath} ({len(all_bars)} rows)")

        except Exception as e:
            print(f"  Error: {e}")

    return paths


# ============================================================
# SOURCE 4: YFINANCE (FREE - DAILY ONLY)
# ============================================================

def download_yfinance(start_date: str = "2010-01-01",
                      end_date: str = "2025-01-01") -> Dict[str, str]:
    """
    Download ES daily data from yfinance.

    Limitations:
        - Daily data only
        - No VWAP
        - Continuous contract approximation (uses ES=F)
        - Volume may be inaccurate

    Returns:
        Dictionary of {timeframe: filepath}
    """
    try:
        import yfinance as yf
    except ImportError:
        print("Install yfinance: pip install yfinance")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename = "ES_daily_yfinance.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print("Downloading ES daily data from yfinance...")

    ticker = yf.Ticker("ES=F")
    df = ticker.history(start=start_date, end=end_date, auto_adjust=False)

    if df.empty:
        print("No data received from yfinance")
        return {}

    all_bars = []
    for idx, row in df.iterrows():
        ts = idx.tz_convert("UTC") if idx.tzinfo else idx.tz_localize("UTC")

        all_bars.append([
            ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            f"{row['Open']:.2f}",
            f"{row['High']:.2f}",
            f"{row['Low']:.2f}",
            f"{row['Close']:.2f}",
            str(int(row['Volume'])),
            "",
            "RTH",
            f"{row['High']:.2f}",
            f"{row['Low']:.2f}",
        ])

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(all_bars)

    print(f"  Saved: {filepath} ({len(all_bars)} rows)")

    return {"daily": filepath}


# ============================================================
# SOURCE 5: TRADINGVIEW (MANUAL EXPORT INSTRUCTIONS)
# ============================================================

def tradingview_instructions() -> str:
    """
    Step-by-step instructions for TradingView CSV export.
    """
    return """
TRADINGVIEW ES DATA EXPORT - STEP BY STEP
==========================================

Prerequisites:
  - TradingView Pro/Pro+/Premium account (free tier has limited exports)

Steps:

1. OPEN CHART
   - Go to tradingview.com
   - Open chart for symbol: ES1! (continuous ES front-month)
   - Or use CME_MINI:ES1! for the official CME feed

2. SET TIMEFRAME
   - Click the timeframe selector (top left)
   - Select desired timeframe (1m, 5m, 15m, 1H, 1D)

3. SET DATE RANGE
   - Right-click on the time axis -> "Go to date"
   - Navigate to your start date (2010-01-01)
   - Zoom out to see the full range

4. EXPORT DATA
   - Click the "Export chart data" button (top right menu, three dots)
   - Or press Ctrl+Shift+E
   - Select "Export chart data to CSV"
   - Save the file

5. RENAME FILE
   - Rename to match schema: ES_{timeframe}_tradingview.csv
   - Example: ES_1min_tradingview.csv

6. CONVERT FORMAT
   - TradingView CSV format:
     time,open,high,low,close,Volume
   - Run this script to convert:

     python es_data_downloader.py --convert-tv path/to/file.csv --timeframe 1min

NOTE: TradingView limits data history:
  - 1min:  ~1 month
  - 5min:  ~3 months
  - 15min: ~6 months
  - 1H:    ~2 years
  - 1D:    ~20 years (best for full history)
"""


# ============================================================
# SOURCE 6: CME DATAMINE (OFFICIAL)
# ============================================================

def cme_datamine_instructions() -> str:
    """
    Instructions for CME DataMine official data.
    """
    return """
CME DATAMINE - OFFICIAL ES DATA
================================

CME DataMine is the official source for CME Group market data.

URL: https://datamine.cmegroup.com/

Steps:

1. Create account at datamine.cmegroup.com

2. Navigate to:
   Market Data -> Historical Data -> E-mini S&P 500

3. Select data type:
   - "Time and Sales" for tick data
   - "End of Day" for daily OHLCV
   - "Intraday" for 1min/5min bars

4. Select date range:
   - Start: 2010-01-01
   - End: current date

5. Purchase and download
   - Pricing varies by data type and date range
   - End of Day: ~$50-100
   - Intraday: ~$200-500+ depending on granularity

6. Data format:
   - CSV with headers
   - Timestamps in Chicago time (CT)
   - Convert to UTC: CT + 5h (EST) or CT + 6h (EDT)

7. Convert using this script:
   python es_data_downloader.py --convert-cme path/to/file.csv --timeframe 1min
"""


# ============================================================
# CONVERTER: TradingView CSV -> Standard Schema
# ============================================================

def convert_tradingview_csv(input_path: str, timeframe: str) -> str:
    """
    Convert TradingView CSV export to standard schema.

    Args:
        input_path: Path to TradingView CSV
        timeframe: Timeframe identifier

    Returns:
        Output filepath
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"ES_{timeframe}_tradingview_converted.csv")

    df = pd.read_csv(input_path)

    # TradingView columns: time, open, high, low, close, Volume
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    all_bars = []

    for _, row in df.iterrows():
        # Parse timestamp
        ts_str = str(row.get("time", row.get("datetime", row.get("date", ""))))

        try:
            ts = pd.Timestamp(ts_str)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert("UTC")
        except Exception:
            continue

        session = classify_session(ts)

        all_bars.append([
            ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            f"{row['open']:.2f}",
            f"{row['high']:.2f}",
            f"{row['low']:.2f}",
            f"{row['close']:.2f}",
            str(int(row.get("volume", row.get("Volume", 0)))),
            "",
            session,
            "", "",
        ])

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(all_bars)

    print(f"Converted: {output_path} ({len(all_bars)} rows)")
    return output_path


# ============================================================
# MAIN CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="ES Futures Data Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python es_data_downloader.py --source polygon --api-key abc123
  python es_data_downloader.py --source ibkr
  python es_data_downloader.py --source databento --api-key abc123
  python es_data_downloader.py --source yfinance
  python es_data_downloader.py --instructions tradingview
  python es_data_downloader.py --instructions cme
  python es_data_downloader.py --convert-tv data.csv --timeframe 1min
        """
    )

    parser.add_argument("--source", choices=["polygon", "ibkr", "databento", "yfinance"],
                        help="Data source to download from")
    parser.add_argument("--api-key", help="API key for the data source")
    parser.add_argument("--start", default="2010-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2025-01-01", help="End date (YYYY-MM-DD)")
    parser.add_argument("--timeframes", nargs="+",
                        default=["1min", "5min", "15min", "1hour", "daily"],
                        help="Timeframes to download")
    parser.add_argument("--instructions", choices=["tradingview", "cme"],
                        help="Print instructions for manual data source")
    parser.add_argument("--convert-tv", help="Convert TradingView CSV to standard schema")
    parser.add_argument("--timeframe", help="Timeframe for conversion", default="1min")

    args = parser.parse_args()

    if args.instructions:
        if args.instructions == "tradingview":
            print(tradingview_instructions())
        elif args.instructions == "cme":
            print(cme_datamine_instructions())
        return

    if args.convert_tv:
        convert_tradingview_csv(args.convert_tv, args.timeframe)
        return

    if not args.source:
        parser.print_help()
        return

    if args.source == "polygon":
        if not args.api_key:
            print("Polygon requires --api-key")
            return
        download_polygon(args.api_key, args.start, args.end, args.timeframes)

    elif args.source == "ibkr":
        download_ibkr(args.timeframes)

    elif args.source == "databento":
        if not args.api_key:
            print("Databento requires --api-key")
            return
        download_databento(args.api_key, args.start, args.end, args.timeframes)

    elif args.source == "yfinance":
        download_yfinance(args.start, args.end)


if __name__ == "__main__":
    main()

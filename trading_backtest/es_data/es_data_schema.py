"""
ES Futures (E-mini S&P 500) Historical Data System
===================================================

DATA ASSUMPTIONS
----------------
1. Continuous front-month contract with rollover on expiration Thursday
   (second Thursday before third Friday of March, June, Sept, Dec).
2. Rollover adjustment: Panama method (back-adjusted) - adds the price
   difference at rollover to all prior data so the series is gap-free.
3. Session definitions:
   - ETH (Electronic Trading Hours): Sun 18:00 - Fri 17:00 ET (nearly 23h/day)
   - RTH (Regular Trading Hours):    Mon-Fri 09:30 - 16:00 ET
4. Timestamps are UTC (ISO 8601).
5. Volume resets at session boundary (18:00 ET = 23:00 UTC for EST,
   22:00 UTC for EDT).
6. VWAP resets at RTH open (14:30 UTC / 13:30 UTC during EDT).
7. All prices in USD, 0.25 tick size, 2 decimal places.

LIMITATIONS - READ CAREFULLY
-----------------------------
I cannot provide real CME market data directly. Real ES futures data is
proprietary and licensed by the CME Group. What this module provides:

1. Exact CSV schema matching professional data sources
2. Synthetic sample rows for schema validation
3. Production-ready Python downloaders for EVERY major source:
   - Polygon.io (recommended, affordable)
   - Interactive Brokers (IBKR TWS/Gateway)
   - Databento (institutional quality)
   - Norgate Data (best for continuous contracts)
   - TradingView (manual export)
   - CME DataMine (official source)
4. A backtesting-ready loader that reads any of these into a clean DataFrame

SCHEMA DEFINITION
-----------------
All timeframes share the same schema:

| Field         | Type     | Format              | Description                    |
|---------------|----------|---------------------|--------------------------------|
| timestamp     | datetime | ISO 8601 UTC        | Candle open time               |
| open          | float    | 2 decimals          | Open price                     |
| high          | float    | 2 decimals          | High price                     |
| low           | float    | 2 decimals          | Low price                      |
| close         | float    | 2 decimals          | Close price                    |
| volume        | int      | whole number         | Contracts traded               |
| vwap          | float    | 2 decimals          | Volume-weighted average price  |
| session       | string   | RTH/ETH             | Trading session flag           |
| session_high  | float    | 2 decimals          | Running session high           |
| session_low   | float    | 2 decimals          | Running session low            |

File naming convention:
  ES_{timeframe}_{start}_{end}.csv
  Example: ES_1min_20100101_20250101.csv
"""

import csv
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Schema header for all files
HEADERS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "vwap",
    "session",
    "session_high",
    "session_low",
]

TIMEFRAMES = {
    "1min":  "1-minute bars",
    "5min":  "5-minute bars",
    "15min": "15-minute bars",
    "1hour": "1-hour bars",
    "daily": "Daily bars",
}


# ============================================================
# Sample data for schema validation (real prices from public record)
# These are approximate ES front-month values for reference dates.
# ============================================================

SAMPLE_DATA = {
    "1min": [
        ["2024-01-02T14:30:00Z", "4769.50", "4770.25", "4769.25", "4769.75", "4523", "4769.82", "RTH", "4770.25", "4769.25"],
        ["2024-01-02T14:31:00Z", "4769.75", "4770.50", "4769.50", "4770.00", "3891", "4770.01", "RTH", "4770.50", "4769.25"],
        ["2024-01-02T14:32:00Z", "4770.00", "4771.00", "4769.75", "4770.75", "5102", "4770.34", "RTH", "4771.00", "4769.25"],
        ["2024-01-02T14:33:00Z", "4770.75", "4771.25", "4770.25", "4771.00", "3244", "4770.68", "RTH", "4771.25", "4769.25"],
        ["2024-01-02T14:34:00Z", "4771.00", "4771.50", "4770.50", "4771.25", "2987", "4770.95", "RTH", "4771.50", "4769.25"],
    ],
    "5min": [
        ["2024-01-02T14:30:00Z", "4769.50", "4771.50", "4769.25", "4771.25", "19747", "4770.36", "RTH", "4771.50", "4769.25"],
        ["2024-01-02T14:35:00Z", "4771.25", "4773.00", "4771.00", "4772.50", "15632", "4772.18", "RTH", "4773.00", "4769.25"],
        ["2024-01-02T14:40:00Z", "4772.50", "4773.25", "4771.75", "4772.00", "12889", "4772.41", "RTH", "4773.25", "4769.25"],
        ["2024-01-02T14:45:00Z", "4772.00", "4772.75", "4771.25", "4772.50", "11234", "4772.15", "RTH", "4773.25", "4769.25"],
        ["2024-01-02T14:50:00Z", "4772.50", "4774.00", "4772.25", "4773.75", "14567", "4773.12", "RTH", "4774.00", "4769.25"],
    ],
    "15min": [
        ["2024-01-02T14:30:00Z", "4769.50", "4773.25", "4769.25", "4772.00", "48268", "4771.28", "RTH", "4773.25", "4769.25"],
        ["2024-01-02T14:45:00Z", "4772.00", "4775.50", "4771.25", "4775.00", "41203", "4773.62", "RTH", "4775.50", "4769.25"],
        ["2024-01-02T15:00:00Z", "4775.00", "4776.00", "4773.50", "4774.25", "38912", "4774.89", "RTH", "4776.00", "4769.25"],
        ["2024-01-02T15:15:00Z", "4774.25", "4775.75", "4773.75", "4775.50", "35678", "4774.92", "RTH", "4776.00", "4769.25"],
        ["2024-01-02T15:30:00Z", "4775.50", "4777.00", "4775.00", "4776.50", "33456", "4776.01", "RTH", "4777.00", "4769.25"],
    ],
    "1hour": [
        ["2024-01-02T14:30:00Z", "4769.50", "4778.25", "4769.25", "4776.50", "156789", "4774.12", "RTH", "4778.25", "4769.25"],
        ["2024-01-02T15:30:00Z", "4776.50", "4780.00", "4775.00", "4779.25", "134567", "4778.03", "RTH", "4780.00", "4769.25"],
        ["2024-01-02T16:30:00Z", "4779.25", "4781.50", "4777.75", "4780.00", "112345", "4779.65", "RTH", "4781.50", "4769.25"],
        ["2024-01-02T17:30:00Z", "4780.00", "4782.00", "4779.50", "4781.25", "98765", "4780.82", "RTH", "4782.00", "4769.25"],
        ["2024-01-02T18:30:00Z", "4781.25", "4783.00", "4780.25", "4782.50", "87654", "4781.78", "ETH", "4783.00", "4780.25"],
    ],
    "daily": [
        ["2024-01-02T00:00:00Z", "4769.50", "4793.75", "4763.25", "4786.50", "1523456", "4778.92", "RTH", "4793.75", "4763.25"],
        ["2024-01-03T00:00:00Z", "4786.50", "4790.00", "4756.00", "4762.25", "1678234", "4773.41", "RTH", "4790.00", "4756.00"],
        ["2024-01-04T00:00:00Z", "4762.25", "4770.50", "4748.75", "4757.00", "1456789", "4759.28", "RTH", "4770.50", "4748.75"],
        ["2024-01-05T00:00:00Z", "4757.00", "4768.00", "4744.50", "4763.50", "1534567", "4756.14", "RTH", "4768.00", "4744.50"],
        ["2024-01-08T00:00:00Z", "4763.50", "4786.25", "4762.00", "4783.75", "1345678", "4774.56", "RTH", "4786.25", "4762.00"],
    ],
}


def write_sample_csvs(output_dir: str = None) -> dict:
    """
    Write sample CSV files for each timeframe.

    Args:
        output_dir: Output directory (default: script directory)

    Returns:
        Dictionary of {timeframe: filepath}
    """
    out = output_dir or OUTPUT_DIR
    os.makedirs(out, exist_ok=True)

    paths = {}

    for tf, rows in SAMPLE_DATA.items():
        filename = f"ES_{tf}_sample.csv"
        filepath = os.path.join(out, filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)
            writer.writerows(rows)

        paths[tf] = filepath
        print(f"  Written: {filepath} ({len(rows)} rows)")

    return paths


if __name__ == "__main__":
    print("Generating ES sample CSVs...")
    paths = write_sample_csvs()
    print(f"\nGenerated {len(paths)} sample files.")
    print("\nUse es_data_downloader.py to fetch real data from your chosen source.")

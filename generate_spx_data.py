#!/usr/bin/env python3
"""
Generate realistic simulated SPX intraday data for backtesting.

Produces 5 years of 1-minute OHLCV bars that mimic real S&P 500 behavior:
- Regular trading hours only (9:30 - 16:00 ET, Mon-Fri)
- Volatility clustering (GARCH-like)
- Intraday volume patterns (U-shape)
- Overnight gaps
- Regime shifts (bull, bear, sideways)
- Proper OHLCV relationships (High >= Open,Close; Low <= Open,Close)

Then resamples into 15m, 1h, and 4h timeframes.

Usage:
    python generate_spx_data.py
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 12345
START_DATE = "2021-01-04"  # ~5 years back from early 2026
END_DATE = "2025-12-31"
INITIAL_PRICE = 3700.0     # SPX was ~3700 at start of 2021
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

# Market hours (ET)
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)
MINUTES_PER_DAY = 390  # 6.5 hours * 60

# US market holidays (major ones, approximate)
US_HOLIDAYS = {
    # 2021
    "2021-01-01", "2021-01-18", "2021-02-15", "2021-04-02", "2021-05-31",
    "2021-07-05", "2021-09-06", "2021-11-25", "2021-12-24",
    # 2022
    "2022-01-17", "2022-02-21", "2022-04-15", "2022-05-30", "2022-06-20",
    "2022-07-04", "2022-09-05", "2022-11-24", "2022-12-26",
    # 2023
    "2023-01-02", "2023-01-16", "2023-02-20", "2023-04-07", "2023-05-29",
    "2023-06-19", "2023-07-04", "2023-09-04", "2023-11-23", "2023-12-25",
    # 2024
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27",
    "2024-06-19", "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25",
    # 2025
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
}


# ---------------------------------------------------------------------------
# Intraday volume profile (U-shape)
# ---------------------------------------------------------------------------

def make_volume_profile(n_minutes: int = MINUTES_PER_DAY) -> np.ndarray:
    """U-shaped intraday volume profile (high at open/close, low midday)."""
    x = np.linspace(0, 1, n_minutes)
    # Bathtub curve: high at edges, low in middle
    profile = 2.5 * np.exp(-8 * x) + 2.0 * np.exp(-8 * (1 - x)) + 0.5
    # Add a small lunch dip
    profile -= 0.3 * np.exp(-50 * (x - 0.45) ** 2)
    profile = np.maximum(profile, 0.2)
    profile /= profile.sum()
    return profile


# ---------------------------------------------------------------------------
# Regime definitions
# ---------------------------------------------------------------------------

REGIMES = [
    # (name, annual_drift, annual_vol, avg_duration_days)
    ("strong_bull",  0.25,  0.12,  120),
    ("mild_bull",    0.10,  0.14,  180),
    ("sideways",     0.02,  0.16,  100),
    ("correction",  -0.10,  0.22,   60),
    ("bear",        -0.25,  0.30,   80),
    ("recovery",     0.30,  0.20,   90),
]


def generate_regime_sequence(rng: np.random.Generator, n_days: int) -> list:
    """Generate a sequence of market regimes covering n_days."""
    regimes = []
    day = 0
    # Start with mild_bull (market was recovering in early 2021)
    regime_idx = 1

    while day < n_days:
        name, drift, vol, avg_dur = REGIMES[regime_idx]
        duration = max(20, int(rng.normal(avg_dur, avg_dur * 0.3)))
        duration = min(duration, n_days - day)
        regimes.append((name, drift, vol, duration))
        day += duration

        # Transition probabilities based on current regime
        if name in ("strong_bull", "mild_bull"):
            weights = [0.15, 0.30, 0.25, 0.20, 0.05, 0.05]
        elif name == "sideways":
            weights = [0.10, 0.25, 0.20, 0.25, 0.10, 0.10]
        elif name in ("correction", "bear"):
            weights = [0.05, 0.10, 0.15, 0.15, 0.20, 0.35]
        else:  # recovery
            weights = [0.25, 0.30, 0.20, 0.10, 0.05, 0.10]

        regime_idx = rng.choice(len(REGIMES), p=weights)

    return regimes


# ---------------------------------------------------------------------------
# Core 1-minute data generation
# ---------------------------------------------------------------------------

def generate_1m_data(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    initial_price: float = INITIAL_PRICE,
    seed: int = SEED,
) -> pd.DataFrame:
    """Generate realistic 1-minute SPX OHLCV data."""
    rng = np.random.default_rng(seed)

    # Build trading day calendar
    all_dates = pd.bdate_range(start_date, end_date, freq="B")
    holidays = {pd.Timestamp(h) for h in US_HOLIDAYS}
    trading_days = [d for d in all_dates if d not in holidays]
    n_days = len(trading_days)

    print(f"Generating {n_days} trading days of 1-minute data...")

    # Regime sequence
    regimes = generate_regime_sequence(rng, n_days)
    print(f"Market regimes: {[(r[0], r[3]) for r in regimes]}")

    # Volume profile
    vol_profile = make_volume_profile()
    base_daily_volume = 3_500_000_000  # ~3.5B shares/day for SPX constituents

    # Pre-allocate arrays
    total_bars = n_days * MINUTES_PER_DAY
    timestamps = []
    opens = np.empty(total_bars)
    highs = np.empty(total_bars)
    lows = np.empty(total_bars)
    closes = np.empty(total_bars)
    volumes = np.empty(total_bars, dtype=np.int64)

    price = initial_price
    bar_idx = 0
    regime_day = 0
    current_regime_idx = 0
    current_regime = regimes[0]
    prev_close = initial_price

    # Volatility state for GARCH-like clustering
    vol_state = current_regime[2] / np.sqrt(252 * MINUTES_PER_DAY)

    for day_i, day in enumerate(trading_days):
        # Check regime transition
        if regime_day >= current_regime[3] and current_regime_idx < len(regimes) - 1:
            current_regime_idx += 1
            current_regime = regimes[current_regime_idx]
            regime_day = 0

        name, annual_drift, annual_vol, _ = current_regime
        minute_drift = annual_drift / (252 * MINUTES_PER_DAY)
        target_vol = annual_vol / np.sqrt(252 * MINUTES_PER_DAY)

        # Overnight gap (drawn from wider distribution)
        gap_vol = annual_vol * 0.3 / np.sqrt(252)
        gap = rng.normal(annual_drift / 252 * 0.3, gap_vol)
        price = prev_close * (1 + gap)

        # Daily volume variation
        daily_vol_mult = rng.lognormal(0, 0.3)

        # Generate minute bars for this day
        dt_base = pd.Timestamp(day).replace(hour=9, minute=30)

        for minute_i in range(MINUTES_PER_DAY):
            # GARCH-like volatility update
            vol_state = 0.94 * vol_state + 0.06 * target_vol
            noise_vol = vol_state * (1 + 0.3 * rng.standard_normal())
            noise_vol = max(noise_vol, target_vol * 0.2)

            # Price return
            ret = minute_drift + noise_vol * rng.standard_normal()

            # Occasional spikes (fat tails)
            if rng.random() < 0.002:
                ret += rng.choice([-1, 1]) * rng.exponential(0.003)

            open_price = price
            close_price = open_price * (1 + ret)

            # Intrabar high/low
            intrabar_range = abs(ret) + noise_vol * abs(rng.standard_normal()) * 0.5
            high_price = max(open_price, close_price) + open_price * intrabar_range * rng.random() * 0.5
            low_price = min(open_price, close_price) - open_price * intrabar_range * rng.random() * 0.5
            low_price = max(low_price, 0.01)

            # Volume
            bar_volume = int(
                base_daily_volume * vol_profile[minute_i]
                * daily_vol_mult
                * (1 + 0.5 * rng.standard_normal())
            )
            bar_volume = max(bar_volume, 1000)

            # Store
            ts = dt_base + timedelta(minutes=minute_i)
            timestamps.append(ts)
            opens[bar_idx] = round(open_price, 2)
            highs[bar_idx] = round(high_price, 2)
            lows[bar_idx] = round(low_price, 2)
            closes[bar_idx] = round(close_price, 2)
            volumes[bar_idx] = bar_volume

            price = close_price
            bar_idx += 1

        prev_close = price
        regime_day += 1

        if (day_i + 1) % 250 == 0:
            print(f"  {day_i + 1}/{n_days} days generated, price: ${price:,.2f}")

    print(f"  Final price: ${price:,.2f} ({(price/initial_price - 1)*100:+.1f}%)")

    df = pd.DataFrame({
        "Date": timestamps[:bar_idx],
        "Open": opens[:bar_idx],
        "High": highs[:bar_idx],
        "Low": lows[:bar_idx],
        "Close": closes[:bar_idx],
        "Volume": volumes[:bar_idx],
    })
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    return df


# ---------------------------------------------------------------------------
# Resample to higher timeframes
# ---------------------------------------------------------------------------

def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample 1m OHLCV data to a higher timeframe.

    Handles market-hours-only data correctly.
    """
    resampled = df.resample(rule).agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }).dropna(subset=["Open"])

    return resampled


TIMEFRAMES = {
    "1m":  None,          # Base data, no resampling
    "15m": "15min",
    "1h":  "1h",
    "4h":  "4h",
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate base 1-minute data
    df_1m = generate_1m_data()

    # Save and resample
    for label, rule in TIMEFRAMES.items():
        if rule is None:
            df = df_1m
        else:
            print(f"Resampling to {label}...")
            df = resample_ohlcv(df_1m, rule)

        # Reset index so Date is a column for CSV
        out = df.copy()
        out.index.name = "Date"
        out = out.reset_index()

        filename = f"SPX_{label}.csv"
        path = os.path.join(OUTPUT_DIR, filename)
        out.to_csv(path, index=False)

        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  Saved: {path} ({len(df):,} bars, {size_mb:.1f} MB)")

    # Print summary
    print(f"\n{'='*55}")
    print(f"  SPX DATA GENERATION COMPLETE")
    print(f"{'='*55}")
    print(f"  Output directory: {OUTPUT_DIR}/")
    print(f"  Files:")
    for label in TIMEFRAMES:
        path = os.path.join(OUTPUT_DIR, f"SPX_{label}.csv")
        if os.path.exists(path):
            n = sum(1 for _ in open(path)) - 1
            sz = os.path.getsize(path) / (1024 * 1024)
            print(f"    SPX_{label}.csv  -  {n:>10,} bars  ({sz:.1f} MB)")
    print(f"  Period: {START_DATE} to {END_DATE}")
    print(f"  Starting price: ${INITIAL_PRICE:,.2f}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()

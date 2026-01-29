"""
ES Futures Backtesting Data Loader
===================================
Production-ready loader that reads ES CSV data (from any source)
into clean, validated pandas DataFrames ready for backtesting.

Features:
  - Loads any timeframe (1min, 5min, 15min, 1hour, daily)
  - Validates data integrity (gaps, spikes, OHLC consistency)
  - Computes session high/low and VWAP if missing
  - Splits into RTH/ETH sessions
  - Provides train/test/OOS splits
  - No look-ahead bias enforcement
  - Resampling between timeframes

Usage:
    from es_data_loader import ESDataLoader

    loader = ESDataLoader("downloaded/ES_1min_polygon.csv")
    df = loader.load()
    rth = loader.rth_only()
    train, val, oos = loader.train_val_oos_split()
"""

import os
import warnings
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class ESDataLoader:
    """
    Backtesting-ready data loader for ES futures CSVs.
    """

    # ES tick size
    TICK_SIZE = 0.25
    POINT_VALUE = 50.0  # $50 per point for ES

    # RTH bounds (UTC, approximate - covers both EST and EDT)
    RTH_START_UTC = time(13, 30)   # EDT RTH start
    RTH_END_UTC = time(21, 0)     # EST RTH end
    RTH_START_EST = time(14, 30)
    RTH_END_EST = time(21, 0)

    # Session boundary (ETH starts at 23:00 UTC / 18:00 ET)
    SESSION_START_UTC = time(23, 0)

    def __init__(self, filepath: str):
        """
        Args:
            filepath: Path to ES CSV file matching the standard schema.
        """
        self.filepath = filepath
        self._df: Optional[pd.DataFrame] = None
        self._validated = False

    def load(self, validate: bool = True) -> pd.DataFrame:
        """
        Load and optionally validate the CSV data.

        Args:
            validate: Run data quality checks

        Returns:
            Clean DataFrame indexed by UTC timestamp
        """
        df = pd.read_csv(self.filepath)

        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Parse timestamp
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp").sort_index()

        # Ensure numeric columns
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Optional columns
        for col in ["vwap", "session_high", "session_low"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Fill session column if missing
        if "session" not in df.columns or df["session"].isna().all():
            df["session"] = df.index.map(self._classify_session)

        # Drop rows with all NaN OHLC
        df = df.dropna(subset=["open", "high", "low", "close"], how="all")

        # Forward-fill small gaps (up to 5 bars)
        df = df.ffill(limit=5)

        # Compute VWAP if missing
        if "vwap" not in df.columns or df["vwap"].isna().all():
            df["vwap"] = self._compute_vwap(df)

        # Compute session high/low if missing
        if "session_high" not in df.columns or df["session_high"].isna().all():
            df = self._compute_session_levels(df)

        self._df = df

        if validate:
            self._validate()

        return df

    @staticmethod
    def _classify_session(ts: pd.Timestamp) -> str:
        """Classify timestamp as RTH or ETH."""
        t = ts.time()
        # Broad RTH window covering both EST and EDT
        if time(13, 30) <= t <= time(21, 0):
            return "RTH"
        return "ETH"

    @staticmethod
    def _compute_vwap(df: pd.DataFrame) -> pd.Series:
        """Compute VWAP from OHLCV data."""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        vol = df["volume"].replace(0, np.nan)

        # Reset VWAP daily
        daily_group = df.index.date
        vwap = pd.Series(index=df.index, dtype=float)

        for date, group in df.groupby(daily_group):
            tp = typical_price.loc[group.index]
            v = vol.loc[group.index]
            cum_tp_vol = (tp * v).cumsum()
            cum_vol = v.cumsum()
            vwap.loc[group.index] = cum_tp_vol / cum_vol

        return vwap

    @staticmethod
    def _compute_session_levels(df: pd.DataFrame) -> pd.DataFrame:
        """Compute running session high and low."""
        daily_group = df.index.date

        session_high = pd.Series(index=df.index, dtype=float)
        session_low = pd.Series(index=df.index, dtype=float)

        for date, group in df.groupby(daily_group):
            idx = group.index
            session_high.loc[idx] = group["high"].cummax()
            session_low.loc[idx] = group["low"].cummin()

        df["session_high"] = session_high
        df["session_low"] = session_low

        return df

    def _validate(self) -> None:
        """Run data quality checks."""
        df = self._df
        issues = []

        # 1. Check OHLC consistency
        bad_hl = (df["high"] < df["low"]).sum()
        if bad_hl > 0:
            issues.append(f"OHLC violation: {bad_hl} bars where high < low")

        bad_oh = (df["open"] > df["high"]).sum()
        if bad_oh > 0:
            issues.append(f"OHLC violation: {bad_oh} bars where open > high")

        bad_ol = (df["open"] < df["low"]).sum()
        if bad_ol > 0:
            issues.append(f"OHLC violation: {bad_ol} bars where open < low")

        bad_ch = (df["close"] > df["high"]).sum()
        if bad_ch > 0:
            issues.append(f"OHLC violation: {bad_ch} bars where close > high")

        bad_cl = (df["close"] < df["low"]).sum()
        if bad_cl > 0:
            issues.append(f"OHLC violation: {bad_cl} bars where close < low")

        # 2. Check for price spikes (>5% move in one bar)
        returns = df["close"].pct_change().abs()
        spikes = (returns > 0.05).sum()
        if spikes > 0:
            issues.append(f"Price spikes: {spikes} bars with >5% move (verify these)")

        # 3. Check for zero/negative volume
        zero_vol = (df["volume"] <= 0).sum()
        if zero_vol > 0:
            issues.append(f"Volume: {zero_vol} bars with zero or negative volume")

        # 4. Check for NaN values
        nan_counts = df[["open", "high", "low", "close", "volume"]].isna().sum()
        for col, count in nan_counts.items():
            if count > 0:
                issues.append(f"Missing data: {count} NaN values in {col}")

        # 5. Check timestamp gaps
        diffs = pd.Series(df.index).diff()
        if len(diffs) > 1:
            median_diff = diffs.median()
            large_gaps = diffs[diffs > median_diff * 10].dropna()
            if len(large_gaps) > 0:
                issues.append(f"Timestamp gaps: {len(large_gaps)} gaps > 10x median interval")

        # Report
        self._validated = True

        if issues:
            print(f"DATA VALIDATION - {len(issues)} issues found:")
            for issue in issues:
                print(f"  WARNING: {issue}")
        else:
            print("DATA VALIDATION PASSED - No issues found")

        # Summary stats
        print(f"\nData Summary:")
        print(f"  Rows:       {len(df):,}")
        print(f"  Date range: {df.index.min()} to {df.index.max()}")
        print(f"  RTH bars:   {(df['session'] == 'RTH').sum():,}")
        print(f"  ETH bars:   {(df['session'] == 'ETH').sum():,}")
        print(f"  Price range: {df['low'].min():.2f} - {df['high'].max():.2f}")

    def get_df(self) -> pd.DataFrame:
        """Get loaded DataFrame (loads if not already loaded)."""
        if self._df is None:
            self.load()
        return self._df

    def rth_only(self) -> pd.DataFrame:
        """Return only RTH (Regular Trading Hours) data."""
        df = self.get_df()
        return df[df["session"] == "RTH"].copy()

    def eth_only(self) -> pd.DataFrame:
        """Return only ETH (Electronic Trading Hours) data."""
        df = self.get_df()
        return df[df["session"] == "ETH"].copy()

    def date_range(self, start: str, end: str) -> pd.DataFrame:
        """
        Filter data to a date range.

        Args:
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)

        Returns:
            Filtered DataFrame
        """
        df = self.get_df()
        mask = (df.index >= pd.Timestamp(start, tz="UTC")) & \
               (df.index <= pd.Timestamp(end, tz="UTC"))
        return df[mask].copy()

    def train_val_oos_split(self,
                            train_end: str = "2020-12-31",
                            val_end: str = "2022-12-31") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train / validation / out-of-sample.

        Default split:
          Train:    2010-01-01 to 2020-12-31  (60%)
          Validate: 2021-01-01 to 2022-12-31  (20%)
          OOS:      2023-01-01 to end          (20%)

        No look-ahead bias: splits are strictly chronological.

        Returns:
            Tuple of (train_df, val_df, oos_df)
        """
        df = self.get_df()

        train = df[df.index <= pd.Timestamp(train_end, tz="UTC")].copy()
        val = df[(df.index > pd.Timestamp(train_end, tz="UTC")) &
                 (df.index <= pd.Timestamp(val_end, tz="UTC"))].copy()
        oos = df[df.index > pd.Timestamp(val_end, tz="UTC")].copy()

        print(f"Train:    {len(train):>8,} bars  ({train.index.min().date()} to {train.index.max().date()})")
        print(f"Validate: {len(val):>8,} bars  ({val.index.min().date()} to {val.index.max().date()})")
        print(f"OOS:      {len(oos):>8,} bars  ({oos.index.min().date()} to {oos.index.max().date()})")

        return train, val, oos

    def resample(self, target_tf: str) -> pd.DataFrame:
        """
        Resample data to a higher timeframe.

        Args:
            target_tf: Target timeframe ('5min', '15min', '1hour', '4hour', 'daily')

        Returns:
            Resampled DataFrame
        """
        tf_map = {
            "5min":  "5min",
            "15min": "15min",
            "30min": "30min",
            "1hour": "1h",
            "4hour": "4h",
            "daily": "1D",
        }

        if target_tf not in tf_map:
            raise ValueError(f"Unknown timeframe: {target_tf}. Use: {list(tf_map.keys())}")

        df = self.get_df()
        freq = tf_map[target_tf]

        resampled = df.resample(freq).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna()

        # Recompute VWAP
        resampled["vwap"] = self._compute_vwap(resampled)

        # Classify sessions
        resampled["session"] = resampled.index.map(self._classify_session)

        # Recompute session levels
        resampled = self._compute_session_levels(resampled)

        return resampled

    def get_daily_bars(self) -> pd.DataFrame:
        """
        Aggregate to daily bars (RTH only for standard daily bars).

        Returns:
            Daily OHLCV DataFrame
        """
        rth = self.rth_only()

        daily = rth.resample("1D").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna()

        return daily

    def get_session_stats(self) -> pd.DataFrame:
        """
        Compute daily session statistics.

        Returns:
            DataFrame with daily stats
        """
        df = self.get_df()

        daily_stats = df.groupby(df.index.date).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            bar_count=("close", "count"),
            range_points=("high", lambda x: x.max() - df.loc[x.index, "low"].min()),
        )

        daily_stats["range_dollars"] = daily_stats["range_points"] * self.POINT_VALUE
        daily_stats["direction"] = np.where(
            daily_stats["close"] > daily_stats["open"], "UP", "DOWN"
        )

        return daily_stats

    def to_backtest_format(self) -> pd.DataFrame:
        """
        Return data in minimal format for backtesting engines.
        Columns: open, high, low, close, volume
        Index: UTC datetime
        """
        df = self.get_df()
        return df[["open", "high", "low", "close", "volume"]].copy()

    @staticmethod
    def detect_gaps(df: pd.DataFrame, threshold_minutes: int = 30) -> pd.DataFrame:
        """
        Find timestamp gaps in the data.

        Args:
            df: Price DataFrame
            threshold_minutes: Minimum gap size to report

        Returns:
            DataFrame of gaps
        """
        diffs = pd.Series(df.index).diff()
        threshold = pd.Timedelta(minutes=threshold_minutes)

        gaps = diffs[diffs > threshold]

        if gaps.empty:
            return pd.DataFrame()

        gap_records = []
        for idx, gap in gaps.items():
            gap_records.append({
                "gap_start": df.index[idx - 1],
                "gap_end": df.index[idx],
                "duration": gap,
                "duration_minutes": gap.total_seconds() / 60,
            })

        return pd.DataFrame(gap_records)


def load_es_data(filepath: str,
                 rth_only: bool = False,
                 start: str = None,
                 end: str = None) -> pd.DataFrame:
    """
    Quick helper to load ES data in one line.

    Args:
        filepath: CSV file path
        rth_only: Only return RTH data
        start: Optional start date filter
        end: Optional end date filter

    Returns:
        Clean DataFrame
    """
    loader = ESDataLoader(filepath)
    df = loader.load()

    if rth_only:
        df = loader.rth_only()

    if start or end:
        if start:
            df = df[df.index >= pd.Timestamp(start, tz="UTC")]
        if end:
            df = df[df.index <= pd.Timestamp(end, tz="UTC")]

    return df


# ============================================================
# EXAMPLE: Complete workflow
# ============================================================

if __name__ == "__main__":
    import sys

    # Generate sample data first
    from es_data_schema import write_sample_csvs, OUTPUT_DIR as SCHEMA_DIR

    print("=" * 60)
    print("ES DATA LOADER - DEMO")
    print("=" * 60)

    # Write sample CSVs
    print("\n1. Writing sample CSVs...")
    paths = write_sample_csvs()

    # Load and validate
    for tf, path in paths.items():
        print(f"\n{'='*60}")
        print(f"Loading {tf} data from: {path}")
        print("=" * 60)

        loader = ESDataLoader(path)
        df = loader.load(validate=True)

        print(f"\nColumns: {list(df.columns)}")
        print(f"\nFirst 3 rows:")
        print(df.head(3).to_string())

    # Show usage examples
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)

    print("""
# Load data
from es_data_loader import ESDataLoader, load_es_data

# Method 1: Full control
loader = ESDataLoader("downloaded/ES_1min_polygon.csv")
df = loader.load()

# Method 2: One-liner
df = load_es_data("downloaded/ES_1min_polygon.csv", rth_only=True)

# RTH only
rth = loader.rth_only()

# Date range
subset = loader.date_range("2023-01-01", "2023-12-31")

# Train/Val/OOS split
train, val, oos = loader.train_val_oos_split()

# Resample 1min -> 15min
df_15min = loader.resample("15min")

# Daily bars
daily = loader.get_daily_bars()

# Minimal format for backtesting
bt_data = loader.to_backtest_format()

# Gap detection
gaps = loader.detect_gaps(df, threshold_minutes=30)
""")

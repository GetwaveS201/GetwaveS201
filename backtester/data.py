"""
Data handling module: CSV loading, validation, cleaning, resampling.

Accepts OHLCV data in CSV format and prepares it for backtesting.
Supports multiple timeframes and batch symbol loading.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}

TIMEFRAME_MAP = {
    "1min": "1T",
    "5min": "5T",
    "15min": "15T",
    "30min": "30T",
    "1h": "1H",
    "4h": "4H",
    "1d": "1D",
    "1w": "1W",
    "1M": "1ME",
}


# ---------------------------------------------------------------------------
# Data quality report
# ---------------------------------------------------------------------------

@dataclass
class DataQualityReport:
    """Summary of data cleaning operations."""

    symbol: str
    original_rows: int = 0
    final_rows: int = 0
    duplicates_removed: int = 0
    nulls_filled: int = 0
    outliers_clipped: int = 0
    gaps_detected: int = 0
    warnings: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"--- Data Quality: {self.symbol} ---",
            f"  Rows: {self.original_rows} -> {self.final_rows}",
            f"  Duplicates removed: {self.duplicates_removed}",
            f"  Nulls forward-filled: {self.nulls_filled}",
            f"  Outliers clipped: {self.outliers_clipped}",
            f"  Gaps detected: {self.gaps_detected}",
        ]
        for w in self.warnings:
            lines.append(f"  WARNING: {w}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core loading and validation
# ---------------------------------------------------------------------------

def load_csv(
    filepath: str | Path,
    symbol: Optional[str] = None,
    date_column: str = "Date",
    parse_dates: bool = True,
) -> pd.DataFrame:
    """Load a single CSV file into a clean OHLCV DataFrame.

    Parameters
    ----------
    filepath : path to CSV
    symbol : optional symbol tag added as a column
    date_column : name of the date/time column in the CSV
    parse_dates : whether to parse the date column

    Returns
    -------
    pd.DataFrame with DatetimeIndex and columns Open, High, Low, Close, Volume
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath)

    # --- Normalise column names (case-insensitive matching) ----------------
    col_map = {}
    lower_cols = {c.lower().strip(): c for c in df.columns}
    for req in REQUIRED_COLUMNS:
        key = req.lower()
        if key in lower_cols:
            col_map[lower_cols[key]] = req
        else:
            # Try common aliases
            aliases = _column_aliases(req)
            found = False
            for alias in aliases:
                if alias in lower_cols:
                    col_map[lower_cols[alias]] = req
                    found = True
                    break
            if not found:
                raise ValueError(
                    f"Required column '{req}' not found. "
                    f"Available: {list(df.columns)}"
                )

    df = df.rename(columns=col_map)

    # --- Parse dates -------------------------------------------------------
    if parse_dates:
        df["Date"] = pd.to_datetime(df["Date"], utc=False)

    df = df.set_index("Date").sort_index()

    # Keep only OHLCV columns (plus any extra user columns)
    ohlcv = ["Open", "High", "Low", "Close", "Volume"]
    extra = [c for c in df.columns if c not in ohlcv]
    df = df[ohlcv + extra]

    # Ensure numeric types
    for col in ohlcv:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if symbol:
        df.attrs["symbol"] = symbol
    else:
        df.attrs["symbol"] = filepath.stem

    return df


def _column_aliases(col: str) -> List[str]:
    """Return common aliases for standard OHLCV columns."""
    aliases = {
        "Date": ["datetime", "time", "timestamp", "date_time", "dt"],
        "Open": ["open_price", "o"],
        "High": ["high_price", "h"],
        "Low": ["low_price", "l"],
        "Close": ["close_price", "c", "adj_close", "adj close", "adjusted_close"],
        "Volume": ["vol", "v", "volume_traded"],
    }
    return aliases.get(col, [])


# ---------------------------------------------------------------------------
# Data cleaning / validation
# ---------------------------------------------------------------------------

def validate_and_clean(
    df: pd.DataFrame,
    max_gap_bars: int = 5,
    clip_outlier_std: float = 8.0,
) -> Tuple[pd.DataFrame, DataQualityReport]:
    """Validate OHLCV data and fix common issues.

    Operations:
    1. Remove duplicate timestamps
    2. Forward-fill small gaps in OHLCV
    3. Clip extreme outliers (> clip_outlier_std standard deviations)
    4. Ensure High >= max(Open, Close) and Low <= min(Open, Close)
    5. Drop rows where Volume < 0

    Returns cleaned DataFrame and a quality report.
    """
    symbol = df.attrs.get("symbol", "unknown")
    report = DataQualityReport(symbol=symbol, original_rows=len(df))

    # 1. Duplicates
    dup_mask = df.index.duplicated(keep="last")
    report.duplicates_removed = int(dup_mask.sum())
    df = df[~dup_mask]

    # 2. Nulls – forward fill then backward fill residuals
    null_count = int(df[["Open", "High", "Low", "Close"]].isna().sum().sum())
    report.nulls_filled = null_count
    df = df.ffill().bfill()

    # 3. Detect gaps in trading days
    if len(df) > 1:
        deltas = df.index.to_series().diff()
        median_delta = deltas.median()
        if median_delta and median_delta.total_seconds() > 0:
            gap_mask = deltas > (median_delta * max_gap_bars)
            report.gaps_detected = int(gap_mask.sum())
            if report.gaps_detected > 0:
                report.warnings.append(
                    f"{report.gaps_detected} gaps > {max_gap_bars}x median bar interval"
                )

    # 4. Clip outliers on returns
    if clip_outlier_std and len(df) > 20:
        returns = df["Close"].pct_change()
        mean_r, std_r = returns.mean(), returns.std()
        if std_r > 0:
            outlier_mask = returns.abs() > (mean_r + clip_outlier_std * std_r)
            report.outliers_clipped = int(outlier_mask.sum())
            if report.outliers_clipped > 0:
                report.warnings.append(
                    f"{report.outliers_clipped} bars with returns > "
                    f"{clip_outlier_std} std devs"
                )

    # 5. Fix OHLC consistency
    df["High"] = df[["Open", "High", "Low", "Close"]].max(axis=1)
    df["Low"] = df[["Open", "High", "Low", "Close"]].min(axis=1)

    # 6. Drop negative volume
    neg_vol = df["Volume"] < 0
    if neg_vol.any():
        report.warnings.append(f"{neg_vol.sum()} rows with negative volume removed")
        df = df[~neg_vol]

    report.final_rows = len(df)

    if report.final_rows == 0:
        raise ValueError(f"No valid data remaining after cleaning for {symbol}")

    logger.info(str(report))
    return df, report


# ---------------------------------------------------------------------------
# Resampling / timeframe conversion
# ---------------------------------------------------------------------------

def resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample OHLCV data to a coarser timeframe.

    Parameters
    ----------
    timeframe : key from TIMEFRAME_MAP, e.g. '1h', '4h', '1d', '1w'
    """
    rule = TIMEFRAME_MAP.get(timeframe)
    if rule is None:
        raise ValueError(
            f"Unknown timeframe '{timeframe}'. "
            f"Choose from: {list(TIMEFRAME_MAP.keys())}"
        )

    resampled = df.resample(rule).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna(subset=["Open"])

    resampled.attrs = df.attrs.copy()
    return resampled


# ---------------------------------------------------------------------------
# Batch loading
# ---------------------------------------------------------------------------

def load_directory(
    directory: str | Path,
    pattern: str = "*.csv",
    clean: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Load all CSV files from a directory.

    Returns dict mapping symbol (filename stem) -> DataFrame.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")

    results: Dict[str, pd.DataFrame] = {}
    for path in sorted(directory.glob(pattern)):
        symbol = path.stem
        try:
            df = load_csv(path, symbol=symbol)
            if clean:
                df, report = validate_and_clean(df)
                logger.info(str(report))
            results[symbol] = df
        except Exception as e:
            logger.warning(f"Skipping {path.name}: {e}")

    if not results:
        raise FileNotFoundError(f"No valid CSV files found in {directory}")

    return results

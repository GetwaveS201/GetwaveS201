"""
Sample data generator for testing the backtesting system.

Generates realistic-looking OHLCV data with configurable properties
(trend, volatility, regime changes) for development and testing.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


def generate_ohlcv(
    symbol: str = "SAMPLE",
    days: int = 750,
    start_price: float = 100.0,
    annual_return: float = 0.08,
    annual_volatility: float = 0.25,
    start_date: str = "2020-01-02",
    regime_changes: bool = True,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Generate synthetic OHLCV data.

    Parameters
    ----------
    symbol : ticker symbol
    days : number of trading days
    start_price : initial price
    annual_return : expected drift (e.g. 0.08 = 8%)
    annual_volatility : annualized volatility (e.g. 0.25 = 25%)
    start_date : first date
    regime_changes : if True, add bull/bear/sideways regimes
    seed : random seed for reproducibility
    """
    if seed is not None:
        np.random.seed(seed)

    # Daily parameters
    dt = 1 / 252
    daily_drift = annual_return * dt
    daily_vol = annual_volatility * np.sqrt(dt)

    # Generate log returns
    if regime_changes:
        returns = _generate_regime_returns(days, daily_drift, daily_vol)
    else:
        returns = np.random.normal(daily_drift, daily_vol, days)

    # Build close prices from returns
    log_prices = np.log(start_price) + np.cumsum(returns)
    close = np.exp(log_prices)

    # Generate OHLV from close
    intraday_vol = daily_vol * 0.6
    high_pct = np.abs(np.random.normal(0, intraday_vol, days)) + 0.001
    low_pct = np.abs(np.random.normal(0, intraday_vol, days)) + 0.001

    high = close * (1 + high_pct)
    low = close * (1 - low_pct)

    # Open: close of previous day + small gap
    gap = np.random.normal(0, daily_vol * 0.2, days)
    open_prices = np.roll(close, 1) * (1 + gap)
    open_prices[0] = start_price

    # Ensure OHLC consistency
    high = np.maximum(high, np.maximum(open_prices, close))
    low = np.minimum(low, np.minimum(open_prices, close))

    # Volume: base + correlated with abs returns
    base_volume = 1_000_000
    vol_noise = np.random.lognormal(0, 0.5, days)
    abs_returns = np.abs(returns)
    volume = (base_volume * vol_noise * (1 + abs_returns * 10)).astype(int)

    # Build DataFrame
    dates = pd.bdate_range(start=start_date, periods=days)
    df = pd.DataFrame({
        "Date": dates,
        "Open": np.round(open_prices, 2),
        "High": np.round(high, 2),
        "Low": np.round(low, 2),
        "Close": np.round(close, 2),
        "Volume": volume,
    })

    return df


def _generate_regime_returns(days: int, base_drift: float, base_vol: float) -> np.ndarray:
    """Generate returns with regime switching (bull/bear/sideways)."""
    returns = np.zeros(days)
    regimes = {
        "bull": (base_drift * 2.5, base_vol * 0.8),
        "bear": (-base_drift * 2.0, base_vol * 1.4),
        "sideways": (0, base_vol * 0.6),
        "crash": (-base_drift * 8.0, base_vol * 3.0),
    }

    i = 0
    while i < days:
        # Pick a regime
        r = np.random.random()
        if r < 0.4:
            regime = "bull"
        elif r < 0.65:
            regime = "bear"
        elif r < 0.92:
            regime = "sideways"
        else:
            regime = "crash"

        # Regime duration
        if regime == "crash":
            duration = np.random.randint(5, 20)
        else:
            duration = np.random.randint(30, 120)

        end = min(i + duration, days)
        drift, vol = regimes[regime]
        returns[i:end] = np.random.normal(drift, vol, end - i)
        i = end

    return returns


def save_sample_data(
    output_dir: str = "data",
    symbols: int = 3,
    days: int = 750,
    seed: int = 42,
) -> list[str]:
    """Generate and save sample CSV files for testing.

    Returns list of file paths created.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    configs = [
        {"symbol": "AAPL_SIM", "start_price": 150, "annual_return": 0.12, "annual_volatility": 0.28},
        {"symbol": "SPY_SIM", "start_price": 400, "annual_return": 0.08, "annual_volatility": 0.18},
        {"symbol": "BTC_SIM", "start_price": 30000, "annual_return": 0.30, "annual_volatility": 0.65},
    ]

    for i, cfg in enumerate(configs[:symbols]):
        df = generate_ohlcv(
            **cfg,
            days=days,
            regime_changes=True,
            seed=seed + i,
        )
        path = os.path.join(output_dir, f"{cfg['symbol']}.csv")
        df.to_csv(path, index=False)
        paths.append(path)
        print(f"  Saved: {path} ({len(df)} bars)")

    return paths


# Allow Optional from typing for older Python
from typing import Optional

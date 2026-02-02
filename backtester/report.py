"""
Reporting module.

Generates trade logs, summary reports, and CSV exports.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .engine import BacktestResult
from .metrics import PerformanceMetrics


# ---------------------------------------------------------------------------
# Trade log CSV
# ---------------------------------------------------------------------------

def export_trade_log(
    result: BacktestResult,
    output_dir: str,
    filename: Optional[str] = None,
) -> str:
    """Export detailed trade log as CSV.

    Returns the path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        symbol = result.data.attrs.get("symbol", "backtest")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{result.strategy_name}_trades_{timestamp}.csv"

    path = os.path.join(output_dir, filename)
    df = result.trade_df

    if df.empty:
        # Write header-only file
        df = pd.DataFrame(columns=[
            "entry_date", "exit_date", "side", "entry_price", "exit_price",
            "shares", "gross_pnl", "net_pnl", "pnl_pct", "commission",
            "slippage_cost", "bars_held", "entry_reason", "exit_reason",
        ])

    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Summary report (text)
# ---------------------------------------------------------------------------

def generate_summary_report(
    result: BacktestResult,
    metrics: PerformanceMetrics,
    output_dir: str,
    filename: Optional[str] = None,
) -> str:
    """Generate a comprehensive text summary report.

    Returns the path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        symbol = result.data.attrs.get("symbol", "backtest")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{result.strategy_name}_report_{timestamp}.txt"

    path = os.path.join(output_dir, filename)

    lines = []
    _add = lines.append

    _add("=" * 65)
    _add("  BACKTEST REPORT")
    _add("=" * 65)
    _add("")
    _add(f"  Strategy:      {result.strategy_name}")
    _add(f"  Symbol:        {result.data.attrs.get('symbol', 'N/A')}")
    _add(f"  Period:        {result.data.index[0]} to {result.data.index[-1]}")
    _add(f"  Bars:          {len(result.data)}")
    _add(f"  Initial Cap:   ${result.config.initial_capital:,.2f}")
    _add(f"  Commission:    {result.config.commission_pct * 100:.2f}%")
    _add(f"  Slippage:      {result.config.slippage_pct * 100:.3f}%")
    _add(f"  Position Size: {result.config.position_size_pct * 100:.0f}%")
    _add(f"  Parameters:    {result.strategy_params}")
    _add("")

    # Performance metrics
    _add(str(metrics))
    _add("")

    # Monthly returns table
    if metrics.monthly_returns is not None and not metrics.monthly_returns.empty:
        _add("-" * 65)
        _add("  MONTHLY RETURNS (%)")
        _add("-" * 65)
        monthly = metrics.monthly_returns
        for date, ret in monthly.items():
            _add(f"  {date.strftime('%Y-%m'):>8s}  {ret:>+8.2f}%")
        _add("")

    # Yearly returns table
    if metrics.yearly_returns is not None and not metrics.yearly_returns.empty:
        _add("-" * 65)
        _add("  YEARLY RETURNS (%)")
        _add("-" * 65)
        yearly = metrics.yearly_returns
        for date, ret in yearly.items():
            _add(f"  {date.strftime('%Y'):>8s}  {ret:>+8.2f}%")
        _add("")

    # Trade summary
    _add("-" * 65)
    _add("  TRADE SUMMARY (first 50 trades)")
    _add("-" * 65)
    _add(f"  {'Entry':<12s} {'Exit':<12s} {'Side':<6s} {'Entry$':>9s} "
         f"{'Exit$':>9s} {'PnL':>10s} {'PnL%':>8s} {'Bars':>5s}")
    _add("  " + "-" * 73)

    for t in result.trades[:50]:
        _add(
            f"  {str(t.entry_date.date()):<12s} {str(t.exit_date.date()):<12s} "
            f"{t.side.value:<6s} {t.entry_price:>9.2f} {t.exit_price:>9.2f} "
            f"{t.net_pnl:>+10.2f} {t.pnl_pct * 100:>+7.2f}% {t.bars_held:>5d}"
        )

    if len(result.trades) > 50:
        _add(f"  ... and {len(result.trades) - 50} more trades")

    _add("")
    _add(f"  Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _add("=" * 65)

    with open(path, "w") as f:
        f.write("\n".join(lines))

    return path


# ---------------------------------------------------------------------------
# Equity curve CSV
# ---------------------------------------------------------------------------

def export_equity_curve(
    result: BacktestResult,
    output_dir: str,
    filename: Optional[str] = None,
) -> str:
    """Export equity curve as CSV."""
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        symbol = result.data.attrs.get("symbol", "backtest")
        filename = f"{symbol}_{result.strategy_name}_equity.csv"

    path = os.path.join(output_dir, filename)

    df = pd.DataFrame({
        "date": result.equity_curve.index,
        "equity": result.equity_curve.values,
    })

    # Add buy-and-hold comparison
    initial = result.config.initial_capital
    bh = initial * (result.data["Close"] / result.data["Close"].iloc[0])
    df["buy_and_hold"] = bh.values

    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Full report generation
# ---------------------------------------------------------------------------

def generate_full_report(
    result: BacktestResult,
    metrics: PerformanceMetrics,
    output_dir: str = "output",
) -> dict:
    """Generate all report artifacts.

    Returns dict of file paths.
    """
    from .visualize import plot_dashboard, plot_monthly_heatmap

    paths = {}
    paths["trade_log"] = export_trade_log(result, output_dir)
    paths["summary"] = generate_summary_report(result, metrics, output_dir)
    paths["equity_csv"] = export_equity_curve(result, output_dir)
    paths["dashboard"] = plot_dashboard(result, metrics, output_dir)
    paths["monthly_heatmap"] = plot_monthly_heatmap(result, metrics, output_dir)

    return paths

"""
Visualization module.

Generates publication-quality charts for backtest analysis.
All charts can be saved as PNG files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/CLI use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .engine import BacktestResult, Side
from .metrics import PerformanceMetrics


# ---------------------------------------------------------------------------
# Style configuration
# ---------------------------------------------------------------------------

STYLE = {
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#e0e0e0",
    "axes.labelcolor": "#e0e0e0",
    "text.color": "#e0e0e0",
    "xtick.color": "#e0e0e0",
    "ytick.color": "#e0e0e0",
    "grid.color": "#2a2a4a",
    "grid.alpha": 0.6,
    "font.size": 10,
    "axes.titlesize": 12,
    "figure.titlesize": 14,
}

COLORS = {
    "equity": "#00d4aa",
    "buy_hold": "#666699",
    "buy": "#00e676",
    "sell": "#ff1744",
    "drawdown": "#ff6b6b",
    "win": "#00d4aa",
    "loss": "#ff1744",
    "price": "#4fc3f7",
    "volume": "#37474f",
}


def _apply_style():
    plt.rcParams.update(STYLE)


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------

def plot_dashboard(
    result: BacktestResult,
    metrics: PerformanceMetrics,
    output_dir: Optional[str] = None,
    show: bool = False,
) -> Optional[str]:
    """Generate a 4-panel dashboard and optionally save to PNG.

    Panels:
    1. Price chart with buy/sell markers
    2. Equity curve vs buy-and-hold
    3. Drawdown chart
    4. Trade PnL distribution
    """
    _apply_style()

    fig, axes = plt.subplots(4, 1, figsize=(16, 20), gridspec_kw={"height_ratios": [3, 2, 1.5, 1.5]})
    fig.suptitle(
        f"{result.strategy_name}  |  {result.data.attrs.get('symbol', '')}  |  "
        f"Return: {metrics.total_return_pct:+.2f}%  Sharpe: {metrics.sharpe_ratio:.2f}  "
        f"MaxDD: {metrics.max_drawdown_pct:.1f}%",
        fontweight="bold",
    )

    _plot_price_with_trades(axes[0], result)
    _plot_equity_curve(axes[1], result, metrics)
    _plot_drawdown(axes[2], result, metrics)
    _plot_trade_distribution(axes[3], result)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    path = None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        symbol = result.data.attrs.get("symbol", "backtest")
        path = os.path.join(output_dir, f"{symbol}_{result.strategy_name}_dashboard.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return path


# ---------------------------------------------------------------------------
# Individual chart functions
# ---------------------------------------------------------------------------

def _plot_price_with_trades(ax: plt.Axes, result: BacktestResult):
    """Price line with buy/sell markers."""
    data = result.data
    ax.plot(data.index, data["Close"], color=COLORS["price"], linewidth=0.8, label="Close")

    # Buy markers
    for t in result.trades:
        marker_color = COLORS["buy"] if t.side == Side.LONG else COLORS["sell"]
        entry_marker = "^" if t.side == Side.LONG else "v"
        exit_marker = "v" if t.side == Side.LONG else "^"

        ax.scatter(t.entry_date, t.entry_price, marker=entry_marker,
                   color=marker_color, s=60, zorder=5, alpha=0.8)
        exit_color = COLORS["buy"] if t.net_pnl > 0 else COLORS["sell"]
        ax.scatter(t.exit_date, t.exit_price, marker=exit_marker,
                   color=exit_color, s=60, zorder=5, alpha=0.8)

    ax.set_title("Price & Trades")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())


def _plot_equity_curve(ax: plt.Axes, result: BacktestResult, metrics: PerformanceMetrics):
    """Equity curve vs buy-and-hold."""
    equity = result.equity_curve
    ax.plot(equity.index, equity.values, color=COLORS["equity"], linewidth=1.2, label="Strategy")

    # Buy and hold line
    initial = result.config.initial_capital
    bh = initial * (result.data["Close"] / result.data["Close"].iloc[0])
    ax.plot(bh.index, bh.values, color=COLORS["buy_hold"], linewidth=0.8,
            linestyle="--", label="Buy & Hold", alpha=0.7)

    ax.axhline(initial, color="#ffffff", linewidth=0.5, linestyle=":", alpha=0.3)
    ax.set_title("Equity Curve")
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))


def _plot_drawdown(ax: plt.Axes, result: BacktestResult, metrics: PerformanceMetrics):
    """Drawdown percentage over time."""
    if metrics.drawdown_series is not None:
        dd = metrics.drawdown_series
        ax.fill_between(dd.index, dd.values, 0, color=COLORS["drawdown"], alpha=0.4)
        ax.plot(dd.index, dd.values, color=COLORS["drawdown"], linewidth=0.6)

    ax.set_title(f"Drawdown (Max: {metrics.max_drawdown_pct:.1f}%)")
    ax.set_ylabel("Drawdown %")
    ax.grid(True, alpha=0.3)


def _plot_trade_distribution(ax: plt.Axes, result: BacktestResult):
    """Histogram of trade PnL."""
    if not result.trades:
        ax.text(0.5, 0.5, "No trades", ha="center", va="center", transform=ax.transAxes)
        return

    pnls = [t.net_pnl for t in result.trades]
    colors = [COLORS["win"] if p > 0 else COLORS["loss"] for p in pnls]

    ax.bar(range(len(pnls)), pnls, color=colors, width=0.8, alpha=0.7)
    ax.axhline(0, color="#ffffff", linewidth=0.5, alpha=0.3)
    ax.set_title("Trade PnL Distribution")
    ax.set_ylabel("Net PnL ($)")
    ax.set_xlabel("Trade #")
    ax.grid(True, alpha=0.3)


# ---------------------------------------------------------------------------
# Monthly heatmap
# ---------------------------------------------------------------------------

def plot_monthly_heatmap(
    result: BacktestResult,
    metrics: PerformanceMetrics,
    output_dir: Optional[str] = None,
    show: bool = False,
) -> Optional[str]:
    """Generate a monthly returns heatmap."""
    _apply_style()

    equity = result.equity_curve
    # Compute monthly returns
    monthly = equity.resample("ME").last().pct_change().dropna() * 100

    if monthly.empty:
        return None

    # Build year x month matrix
    df_m = pd.DataFrame({"return": monthly.values}, index=monthly.index)
    df_m["year"] = df_m.index.year
    df_m["month"] = df_m.index.month
    pivot = df_m.pivot_table(values="return", index="year", columns="month", aggfunc="sum")
    pivot.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][:len(pivot.columns)]

    fig, ax = plt.subplots(figsize=(14, max(4, len(pivot) * 0.6 + 1)))
    fig.suptitle(f"Monthly Returns (%) - {result.strategy_name}", fontweight="bold")

    # Simple colored table
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto",
                   vmin=-10, vmax=10)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    # Annotate cells
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if not np.isnan(val):
                color = "black" if abs(val) < 5 else "white"
                ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                        color=color, fontsize=8, fontweight="bold")

    plt.colorbar(im, ax=ax, shrink=0.8, label="Return %")
    plt.tight_layout()

    path = None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        symbol = result.data.attrs.get("symbol", "backtest")
        path = os.path.join(output_dir, f"{symbol}_{result.strategy_name}_monthly.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return path


# ---------------------------------------------------------------------------
# Optimization surface plot
# ---------------------------------------------------------------------------

def plot_optimization_surface(
    param1_name: str,
    param2_name: str,
    param1_values: list,
    param2_values: list,
    metric_values: np.ndarray,
    metric_name: str = "Sharpe Ratio",
    output_dir: Optional[str] = None,
    show: bool = False,
) -> Optional[str]:
    """Plot a 2D heatmap of optimization results."""
    _apply_style()

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.suptitle(f"Optimization: {metric_name}", fontweight="bold")

    im = ax.imshow(metric_values, cmap="RdYlGn", aspect="auto",
                   origin="lower")

    ax.set_xticks(range(len(param2_values)))
    ax.set_xticklabels([str(v) for v in param2_values], rotation=45)
    ax.set_yticks(range(len(param1_values)))
    ax.set_yticklabels([str(v) for v in param1_values])
    ax.set_xlabel(param2_name)
    ax.set_ylabel(param1_name)

    plt.colorbar(im, ax=ax, label=metric_name)
    plt.tight_layout()

    path = None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"optimization_{param1_name}_{param2_name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return path

"""
Performance metrics module.

Computes all standard trading statistics from backtest results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .engine import BacktestResult, Trade, Side


# ---------------------------------------------------------------------------
# Core metrics dataclass
# ---------------------------------------------------------------------------

@dataclass
class PerformanceMetrics:
    """Complete set of performance statistics."""

    # Returns
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0
    buy_and_hold_return_pct: float = 0.0
    excess_return_pct: float = 0.0

    # Risk
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_days: int = 0
    volatility_annualized: float = 0.0
    downside_deviation: float = 0.0

    # Risk-adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trade stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    avg_trade_pnl: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_bars_held: float = 0.0
    avg_winner_bars: float = 0.0
    avg_loser_bars: float = 0.0

    # Streaks
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    # Costs
    total_commissions: float = 0.0
    total_slippage: float = 0.0

    # Long/Short breakdown
    long_trades: int = 0
    short_trades: int = 0
    long_win_rate: float = 0.0
    short_win_rate: float = 0.0
    long_pnl: float = 0.0
    short_pnl: float = 0.0

    # Time-based
    monthly_returns: Optional[pd.Series] = field(default=None, repr=False)
    yearly_returns: Optional[pd.Series] = field(default=None, repr=False)

    # Equity / drawdown series
    drawdown_series: Optional[pd.Series] = field(default=None, repr=False)

    def summary_dict(self) -> Dict[str, str]:
        """Return a formatted dict suitable for display."""
        return {
            "Total Return": f"{self.total_return_pct:+.2f}%",
            "Annualized Return": f"{self.annualized_return_pct:+.2f}%",
            "Buy & Hold Return": f"{self.buy_and_hold_return_pct:+.2f}%",
            "Excess vs B&H": f"{self.excess_return_pct:+.2f}%",
            "Max Drawdown": f"{self.max_drawdown_pct:.2f}%",
            "Max DD Duration": f"{self.max_drawdown_duration_days} days",
            "Sharpe Ratio": f"{self.sharpe_ratio:.3f}",
            "Sortino Ratio": f"{self.sortino_ratio:.3f}",
            "Calmar Ratio": f"{self.calmar_ratio:.3f}",
            "Volatility (ann.)": f"{self.volatility_annualized:.2f}%",
            "Total Trades": str(self.total_trades),
            "Win Rate": f"{self.win_rate:.1f}%",
            "Profit Factor": f"{self.profit_factor:.2f}",
            "Avg Win": f"${self.avg_win:,.2f} ({self.avg_win_pct:+.2f}%)",
            "Avg Loss": f"${self.avg_loss:,.2f} ({self.avg_loss_pct:+.2f}%)",
            "Largest Win": f"${self.largest_win:,.2f}",
            "Largest Loss": f"${self.largest_loss:,.2f}",
            "Avg Bars Held": f"{self.avg_bars_held:.1f}",
            "Consec. Wins": str(self.max_consecutive_wins),
            "Consec. Losses": str(self.max_consecutive_losses),
            "Total Commissions": f"${self.total_commissions:,.2f}",
            "Total Slippage": f"${self.total_slippage:,.2f}",
            "Long Trades": f"{self.long_trades} (WR: {self.long_win_rate:.1f}%, PnL: ${self.long_pnl:,.2f})",
            "Short Trades": f"{self.short_trades} (WR: {self.short_win_rate:.1f}%, PnL: ${self.short_pnl:,.2f})",
        }

    def __str__(self) -> str:
        lines = ["=" * 55, "  PERFORMANCE REPORT", "=" * 55]
        for k, v in self.summary_dict().items():
            lines.append(f"  {k:<22s} {v}")
        lines.append("=" * 55)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------

def compute_metrics(result: BacktestResult) -> PerformanceMetrics:
    """Compute all metrics from a BacktestResult."""
    m = PerformanceMetrics()
    equity = result.equity_curve
    trades = result.trades
    cfg = result.config
    data = result.data

    if equity.empty:
        return m

    # -- Returns -----------------------------------------------------------
    initial = cfg.initial_capital
    final = equity.iloc[-1]
    m.total_return_pct = ((final - initial) / initial) * 100

    # Annualized
    days = (equity.index[-1] - equity.index[0]).days
    years = max(days / 365.25, 1 / 365.25)
    if initial > 0 and final > 0:
        m.annualized_return_pct = ((final / initial) ** (1 / years) - 1) * 100

    # Buy & hold
    bh_start = data["Close"].iloc[0]
    bh_end = data["Close"].iloc[-1]
    m.buy_and_hold_return_pct = ((bh_end - bh_start) / bh_start) * 100
    m.excess_return_pct = m.total_return_pct - m.buy_and_hold_return_pct

    # -- Drawdown ----------------------------------------------------------
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max * 100
    m.drawdown_series = drawdown
    m.max_drawdown_pct = abs(drawdown.min())

    # Max drawdown duration
    in_dd = equity < running_max
    if in_dd.any():
        dd_groups = (~in_dd).cumsum()
        dd_durations = in_dd.groupby(dd_groups).sum()
        if len(dd_durations) > 0:
            # Convert bar count to approximate days
            if len(equity) > 1:
                avg_bar_days = days / len(equity)
                m.max_drawdown_duration_days = int(dd_durations.max() * avg_bar_days)

    # -- Risk metrics ------------------------------------------------------
    returns = equity.pct_change().dropna()
    if len(returns) > 1:
        # Estimate periods per year
        if days > 0:
            periods_per_year = len(returns) / years
        else:
            periods_per_year = 252

        m.volatility_annualized = float(returns.std() * np.sqrt(periods_per_year) * 100)

        # Sharpe
        rf_per_period = cfg.risk_free_rate / periods_per_year
        excess = returns - rf_per_period
        if returns.std() > 0:
            m.sharpe_ratio = float(excess.mean() / returns.std() * np.sqrt(periods_per_year))

        # Sortino
        downside = returns[returns < 0]
        if len(downside) > 0 and downside.std() > 0:
            m.downside_deviation = float(downside.std() * np.sqrt(periods_per_year) * 100)
            m.sortino_ratio = float(excess.mean() / downside.std() * np.sqrt(periods_per_year))

        # Calmar
        if m.max_drawdown_pct > 0:
            m.calmar_ratio = m.annualized_return_pct / m.max_drawdown_pct

    # -- Trade statistics --------------------------------------------------
    m.total_trades = len(trades)
    if not trades:
        return m

    net_pnls = [t.net_pnl for t in trades]
    pnl_pcts = [t.pnl_pct for t in trades]
    wins = [t for t in trades if t.net_pnl > 0]
    losses = [t for t in trades if t.net_pnl <= 0]

    m.winning_trades = len(wins)
    m.losing_trades = len(losses)
    m.win_rate = (len(wins) / len(trades)) * 100 if trades else 0

    # Profit factor
    gross_profit = sum(t.net_pnl for t in wins)
    gross_loss = abs(sum(t.net_pnl for t in losses))
    m.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Averages
    m.avg_win = np.mean([t.net_pnl for t in wins]) if wins else 0
    m.avg_loss = np.mean([t.net_pnl for t in losses]) if losses else 0
    m.avg_win_pct = np.mean([t.pnl_pct * 100 for t in wins]) if wins else 0
    m.avg_loss_pct = np.mean([t.pnl_pct * 100 for t in losses]) if losses else 0
    m.avg_trade_pnl = np.mean(net_pnls)
    m.largest_win = max(net_pnls)
    m.largest_loss = min(net_pnls)
    m.avg_bars_held = np.mean([t.bars_held for t in trades])
    m.avg_winner_bars = np.mean([t.bars_held for t in wins]) if wins else 0
    m.avg_loser_bars = np.mean([t.bars_held for t in losses]) if losses else 0

    # Consecutive wins/losses
    m.max_consecutive_wins = _max_streak(trades, winning=True)
    m.max_consecutive_losses = _max_streak(trades, winning=False)

    # Costs
    m.total_commissions = sum(t.commission for t in trades)
    m.total_slippage = sum(t.slippage_cost for t in trades)

    # Long / Short breakdown
    long_trades = [t for t in trades if t.side == Side.LONG]
    short_trades = [t for t in trades if t.side == Side.SHORT]
    m.long_trades = len(long_trades)
    m.short_trades = len(short_trades)
    long_wins = [t for t in long_trades if t.net_pnl > 0]
    short_wins = [t for t in short_trades if t.net_pnl > 0]
    m.long_win_rate = (len(long_wins) / len(long_trades) * 100) if long_trades else 0
    m.short_win_rate = (len(short_wins) / len(short_trades) * 100) if short_trades else 0
    m.long_pnl = sum(t.net_pnl for t in long_trades)
    m.short_pnl = sum(t.net_pnl for t in short_trades)

    # -- Monthly / Yearly returns -----------------------------------------
    m.monthly_returns = _period_returns(equity, "ME")
    m.yearly_returns = _period_returns(equity, "YE")

    return m


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _max_streak(trades: List[Trade], winning: bool) -> int:
    streak = 0
    max_streak = 0
    for t in trades:
        is_win = t.net_pnl > 0
        if is_win == winning:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


def _period_returns(equity: pd.Series, freq: str) -> pd.Series:
    """Compute returns grouped by period (month or year)."""
    resampled = equity.resample(freq).last().dropna()
    returns = resampled.pct_change().dropna() * 100
    return returns

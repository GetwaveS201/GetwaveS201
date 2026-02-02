"""
Core backtesting engine.

Executes strategies bar-by-bar, manages positions, tracks equity, and
records every trade with full metadata.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class Side(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"
    NONE = "NONE"


@dataclass
class Trade:
    """Record of a single completed round-trip trade."""

    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    side: Side
    entry_price: float
    exit_price: float
    shares: float
    pnl: float
    pnl_pct: float
    commission: float
    slippage_cost: float
    bars_held: int
    entry_reason: str = ""
    exit_reason: str = ""

    @property
    def net_pnl(self) -> float:
        return self.pnl - self.commission - self.slippage_cost


@dataclass
class Position:
    """An open position."""

    side: Side
    entry_date: pd.Timestamp
    entry_price: float
    shares: float
    entry_reason: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class BacktestConfig:
    """All configurable parameters for a backtest run."""

    initial_capital: float = 100_000.0
    commission_pct: float = 0.001  # 0.1% per trade (each way)
    slippage_pct: float = 0.0005  # 0.05% per trade
    position_size_pct: float = 1.0  # fraction of equity per trade
    max_positions: int = 1
    allow_short: bool = True
    risk_free_rate: float = 0.02  # for Sharpe
    margin_requirement: float = 1.0  # 1.0 = no leverage


# ---------------------------------------------------------------------------
# Strategy base class
# ---------------------------------------------------------------------------

class Strategy(ABC):
    """Base class every strategy must implement.

    Subclass this and override ``init()`` and ``next()``.
    """

    # Parameters dict – override in subclass or set via optimize()
    params: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        self.params = {**self.__class__.params, **kwargs}
        self._indicators: Dict[str, pd.Series] = {}

    # ------------------------------------------------------------------
    # User-defined hooks
    # ------------------------------------------------------------------

    def init(self, data: pd.DataFrame) -> None:
        """Called once before the backtest. Pre-compute indicators here.

        Store them via ``self.add_indicator(name, series)``.
        """

    @abstractmethod
    def next(self, row: pd.Series, indicators: Dict[str, float], ctx: "StrategyContext") -> SignalType:
        """Called for each bar. Return a SignalType.

        Parameters
        ----------
        row : current bar (Open, High, Low, Close, Volume)
        indicators : dict of indicator values at current bar
        ctx : context object with equity, position info, etc.
        """
        ...

    def on_trade(self, trade: Trade) -> None:
        """Optional callback after a trade closes."""

    # ------------------------------------------------------------------
    # Indicator helpers
    # ------------------------------------------------------------------

    def add_indicator(self, name: str, series: pd.Series) -> None:
        self._indicators[name] = series

    def sma(self, series: pd.Series, period: int) -> pd.Series:
        return series.rolling(period).mean()

    def ema(self, series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    def rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    def atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift(1)).abs()
        low_close = (df["Low"] - df["Close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def bollinger_bands(
        self, series: pd.Series, period: int = 20, num_std: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        mid = series.rolling(period).mean()
        std = series.rolling(period).std()
        return mid + num_std * std, mid, mid - num_std * std

    def macd(
        self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram


@dataclass
class StrategyContext:
    """Read-only context passed to Strategy.next() each bar."""

    equity: float
    cash: float
    position: Optional[Position]
    open_positions: int
    bar_index: int
    total_bars: int
    current_date: pd.Timestamp


# ---------------------------------------------------------------------------
# Backtest Engine
# ---------------------------------------------------------------------------

class BacktestEngine:
    """Event-driven backtesting engine.

    Usage::

        engine = BacktestEngine(config)
        result = engine.run(data, strategy)
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def run(self, data: pd.DataFrame, strategy: Strategy) -> "BacktestResult":
        """Run the backtest and return results."""
        cfg = self.config

        # Initialise state
        cash = cfg.initial_capital
        equity_curve: List[float] = []
        equity_dates: List[pd.Timestamp] = []
        trades: List[Trade] = []
        position: Optional[Position] = None
        bar_count = len(data)

        # Let strategy compute indicators
        strategy.init(data)
        indicators = strategy._indicators

        # Pre-build indicator lookup (index -> dict)
        ind_values_at: Dict[int, Dict[str, float]] = {}
        for i in range(bar_count):
            vals = {}
            for name, series in indicators.items():
                try:
                    vals[name] = float(series.iloc[i])
                except (IndexError, ValueError):
                    vals[name] = np.nan
            ind_values_at[i] = vals

        # ---- Main loop ---------------------------------------------------
        for i in range(bar_count):
            row = data.iloc[i]
            date = data.index[i]

            # Build context
            pos_equity = _position_equity(position, row["Close"]) if position else 0.0
            equity = cash + pos_equity
            ctx = StrategyContext(
                equity=equity,
                cash=cash,
                position=position,
                open_positions=1 if position else 0,
                bar_index=i,
                total_bars=bar_count,
                current_date=date,
            )

            # Check stop-loss / take-profit on open position
            if position:
                closed, trade, cash_delta = self._check_exit_orders(
                    position, row, date, i, data
                )
                if closed:
                    cash += cash_delta
                    trades.append(trade)
                    strategy.on_trade(trade)
                    position = None

            # Get strategy signal
            signal = strategy.next(row, ind_values_at.get(i, {}), ctx)

            # Execute signal
            if position is None and signal in (SignalType.BUY, SignalType.SHORT):
                position, cash = self._open_position(
                    signal, row, date, cash, equity, strategy
                )
            elif position and signal in (SignalType.SELL, SignalType.COVER):
                trade, cash = self._close_position(position, row, date, i, data, signal.name)
                trades.append(trade)
                strategy.on_trade(trade)
                position = None

            # Record equity
            pos_equity = _position_equity(position, row["Close"]) if position else 0.0
            equity_curve.append(cash + pos_equity)
            equity_dates.append(date)

        # Close any remaining position at last bar
        if position is not None:
            last_row = data.iloc[-1]
            last_date = data.index[-1]
            trade, cash = self._close_position(
                position, last_row, last_date, bar_count - 1, data, "END_OF_DATA"
            )
            trades.append(trade)
            equity_curve[-1] = cash

        equity_series = pd.Series(equity_curve, index=equity_dates, name="Equity")

        return BacktestResult(
            trades=trades,
            equity_curve=equity_series,
            data=data,
            config=cfg,
            strategy_name=strategy.__class__.__name__,
            strategy_params=dict(strategy.params),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open_position(
        self,
        signal: SignalType,
        row: pd.Series,
        date: pd.Timestamp,
        cash: float,
        equity: float,
        strategy: Strategy,
    ) -> Tuple[Position, float]:
        cfg = self.config
        side = Side.LONG if signal == SignalType.BUY else Side.SHORT

        if side == Side.SHORT and not cfg.allow_short:
            return None, cash  # type: ignore[return-value]

        price = row["Close"]
        slippage = price * cfg.slippage_pct
        fill_price = price + slippage if side == Side.LONG else price - slippage

        available = equity * cfg.position_size_pct / cfg.margin_requirement
        commission = available * cfg.commission_pct
        investable = available - commission
        shares = investable / fill_price if fill_price > 0 else 0

        if shares <= 0:
            return None, cash  # type: ignore[return-value]

        cost = shares * fill_price + commission
        cash -= cost

        pos = Position(
            side=side,
            entry_date=date,
            entry_price=fill_price,
            shares=shares,
            entry_reason=signal.name,
        )

        # Let strategy set stop/TP via params
        if "stop_loss_pct" in strategy.params:
            sl_pct = strategy.params["stop_loss_pct"]
            if side == Side.LONG:
                pos.stop_loss = fill_price * (1 - sl_pct)
            else:
                pos.stop_loss = fill_price * (1 + sl_pct)

        if "take_profit_pct" in strategy.params:
            tp_pct = strategy.params["take_profit_pct"]
            if side == Side.LONG:
                pos.take_profit = fill_price * (1 + tp_pct)
            else:
                pos.take_profit = fill_price * (1 - tp_pct)

        return pos, cash

    def _close_position(
        self,
        position: Position,
        row: pd.Series,
        date: pd.Timestamp,
        bar_idx: int,
        data: pd.DataFrame,
        reason: str,
    ) -> Tuple[Trade, float]:
        cfg = self.config
        price = row["Close"]
        slippage = price * cfg.slippage_pct
        if position.side == Side.LONG:
            fill_price = price - slippage
        else:
            fill_price = price + slippage

        commission = position.shares * fill_price * cfg.commission_pct
        slippage_cost = position.shares * abs(slippage)

        if position.side == Side.LONG:
            gross_pnl = (fill_price - position.entry_price) * position.shares
        else:
            gross_pnl = (position.entry_price - fill_price) * position.shares

        pnl_pct = gross_pnl / (position.entry_price * position.shares) if position.entry_price else 0
        entry_idx = data.index.get_loc(position.entry_date)
        if isinstance(entry_idx, slice):
            entry_idx = entry_idx.start
        bars_held = bar_idx - entry_idx

        proceeds = position.shares * fill_price - commission
        # For short: we received cash at entry, now we buy back
        # Simplification: cash adjustment = proceeds for long, gross_pnl + original cost for short
        if position.side == Side.LONG:
            cash_back = proceeds
        else:
            # Return margin + profit (or - loss)
            cash_back = position.shares * position.entry_price + gross_pnl - commission

        trade = Trade(
            entry_date=position.entry_date,
            exit_date=date,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=fill_price,
            shares=position.shares,
            pnl=gross_pnl,
            pnl_pct=pnl_pct,
            commission=commission,
            slippage_cost=slippage_cost,
            bars_held=bars_held,
            entry_reason=position.entry_reason,
            exit_reason=reason,
        )

        return trade, cash_back

    def _check_exit_orders(
        self,
        position: Position,
        row: pd.Series,
        date: pd.Timestamp,
        bar_idx: int,
        data: pd.DataFrame,
    ) -> Tuple[bool, Optional[Trade], float]:
        """Check stop-loss and take-profit against the current bar's High/Low."""
        triggered = False
        exit_price = 0.0
        reason = ""

        if position.side == Side.LONG:
            if position.stop_loss and row["Low"] <= position.stop_loss:
                exit_price = position.stop_loss
                reason = "STOP_LOSS"
                triggered = True
            elif position.take_profit and row["High"] >= position.take_profit:
                exit_price = position.take_profit
                reason = "TAKE_PROFIT"
                triggered = True
        else:  # SHORT
            if position.stop_loss and row["High"] >= position.stop_loss:
                exit_price = position.stop_loss
                reason = "STOP_LOSS"
                triggered = True
            elif position.take_profit and row["Low"] <= position.take_profit:
                exit_price = position.take_profit
                reason = "TAKE_PROFIT"
                triggered = True

        if not triggered:
            return False, None, 0.0

        # Build a synthetic row at the exit price
        cfg = self.config
        slippage = exit_price * cfg.slippage_pct
        if position.side == Side.LONG:
            fill_price = exit_price - slippage
        else:
            fill_price = exit_price + slippage

        commission = position.shares * fill_price * cfg.commission_pct
        slippage_cost = position.shares * abs(slippage)

        if position.side == Side.LONG:
            gross_pnl = (fill_price - position.entry_price) * position.shares
        else:
            gross_pnl = (position.entry_price - fill_price) * position.shares

        pnl_pct = gross_pnl / (position.entry_price * position.shares) if position.entry_price else 0
        entry_idx = data.index.get_loc(position.entry_date)
        if isinstance(entry_idx, slice):
            entry_idx = entry_idx.start
        bars_held = bar_idx - entry_idx

        if position.side == Side.LONG:
            cash_back = position.shares * fill_price - commission
        else:
            cash_back = position.shares * position.entry_price + gross_pnl - commission

        trade = Trade(
            entry_date=position.entry_date,
            exit_date=date,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=fill_price,
            shares=position.shares,
            pnl=gross_pnl,
            pnl_pct=pnl_pct,
            commission=commission,
            slippage_cost=slippage_cost,
            bars_held=bars_held,
            entry_reason=position.entry_reason,
            exit_reason=reason,
        )

        return True, trade, cash_back


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _position_equity(position: Position, current_price: float) -> float:
    """Mark-to-market value of an open position."""
    if position.side == Side.LONG:
        return position.shares * current_price
    else:
        # Short: value = entry_value + (entry_price - current_price) * shares
        return position.shares * position.entry_price + (
            position.entry_price - current_price
        ) * position.shares


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    """Container holding all backtest outputs."""

    trades: List[Trade]
    equity_curve: pd.Series
    data: pd.DataFrame
    config: BacktestConfig
    strategy_name: str
    strategy_params: Dict[str, Any]

    @property
    def trade_df(self) -> pd.DataFrame:
        """Return trades as a DataFrame."""
        if not self.trades:
            return pd.DataFrame()
        records = []
        for t in self.trades:
            records.append({
                "entry_date": t.entry_date,
                "exit_date": t.exit_date,
                "side": t.side.value,
                "entry_price": round(t.entry_price, 4),
                "exit_price": round(t.exit_price, 4),
                "shares": round(t.shares, 4),
                "gross_pnl": round(t.pnl, 2),
                "net_pnl": round(t.net_pnl, 2),
                "pnl_pct": round(t.pnl_pct * 100, 2),
                "commission": round(t.commission, 2),
                "slippage_cost": round(t.slippage_cost, 2),
                "bars_held": t.bars_held,
                "entry_reason": t.entry_reason,
                "exit_reason": t.exit_reason,
            })
        return pd.DataFrame(records)

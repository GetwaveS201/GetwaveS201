"""
Donchian Channel Breakout Strategy.

Classic trend-following system: enter on N-bar high/low breakout,
exit on shorter M-bar breakout in the opposite direction.
"""

from typing import Any, Dict

import pandas as pd
import numpy as np

from ..engine import SignalType, Side, Strategy, StrategyContext


class DonchianBreakout(Strategy):
    """Donchian channel breakout (turtle trading variant).

    Parameters
    ----------
    entry_period : int
        Lookback for entry channel (default: 20)
    exit_period : int
        Lookback for exit channel (default: 10)
    use_short : bool
        Whether to take short positions (default: True)
    atr_period : int
        ATR period for volatility filter (default: 14)
    """

    params = {
        "entry_period": 20,
        "exit_period": 10,
        "use_short": True,
        "atr_period": 14,
    }

    def init(self, data: pd.DataFrame) -> None:
        entry_p = self.params["entry_period"]
        exit_p = self.params["exit_period"]

        # Shift by 1 so we compare against the *previous* bar's channel
        self.add_indicator("entry_high", data["High"].rolling(entry_p).max().shift(1))
        self.add_indicator("entry_low", data["Low"].rolling(entry_p).min().shift(1))
        self.add_indicator("exit_high", data["High"].rolling(exit_p).max().shift(1))
        self.add_indicator("exit_low", data["Low"].rolling(exit_p).min().shift(1))
        self.add_indicator("atr", self.atr(data, self.params["atr_period"]))

    def next(self, row: pd.Series, indicators: Dict[str, float], ctx: StrategyContext) -> SignalType:
        entry_high = indicators.get("entry_high")
        entry_low = indicators.get("entry_low")
        exit_high = indicators.get("exit_high")
        exit_low = indicators.get("exit_low")

        for val in [entry_high, entry_low, exit_high, exit_low]:
            if val is None or pd.isna(val):
                return SignalType.NONE

        close = row["Close"]
        has_position = ctx.position is not None

        if not has_position:
            if close > entry_high:
                return SignalType.BUY
            elif close < entry_low and self.params.get("use_short", True):
                return SignalType.SHORT
        else:
            if ctx.position.side == Side.LONG and close <= exit_low:
                return SignalType.SELL
            elif ctx.position.side == Side.SHORT and close >= exit_high:
                return SignalType.COVER

        return SignalType.NONE

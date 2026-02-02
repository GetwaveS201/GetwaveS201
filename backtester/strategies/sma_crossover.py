"""
SMA Crossover Strategy.

Classic dual moving average crossover system.
Goes long when fast SMA crosses above slow SMA; exits when it crosses below.
Optionally shorts on the reverse cross.
"""

from typing import Any, Dict

import pandas as pd

from ..engine import SignalType, Strategy, StrategyContext


class SMACrossover(Strategy):
    """Dual SMA crossover strategy.

    Parameters
    ----------
    fast_period : int
        Fast moving average period (default: 10)
    slow_period : int
        Slow moving average period (default: 30)
    use_short : bool
        Whether to take short positions (default: False)
    stop_loss_pct : float, optional
        Stop loss percentage (e.g. 0.05 = 5%)
    take_profit_pct : float, optional
        Take profit percentage
    """

    params = {
        "fast_period": 10,
        "slow_period": 30,
        "use_short": False,
    }

    def init(self, data: pd.DataFrame) -> None:
        close = data["Close"]
        fast = self.params["fast_period"]
        slow = self.params["slow_period"]

        self.add_indicator("sma_fast", self.sma(close, fast))
        self.add_indicator("sma_slow", self.sma(close, slow))

    def next(self, row: pd.Series, indicators: Dict[str, float], ctx: StrategyContext) -> SignalType:
        fast = indicators.get("sma_fast")
        slow = indicators.get("sma_slow")

        if fast is None or slow is None:
            return SignalType.NONE
        if pd.isna(fast) or pd.isna(slow):
            return SignalType.NONE

        has_position = ctx.position is not None

        if not has_position:
            if fast > slow:
                return SignalType.BUY
            elif fast < slow and self.params.get("use_short", False):
                return SignalType.SHORT
        else:
            from ..engine import Side
            if ctx.position.side == Side.LONG and fast < slow:
                return SignalType.SELL
            elif ctx.position.side == Side.SHORT and fast > slow:
                return SignalType.COVER

        return SignalType.NONE

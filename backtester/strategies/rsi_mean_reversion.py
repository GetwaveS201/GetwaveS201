"""
RSI Mean Reversion Strategy.

Buys when RSI drops below oversold level, sells when RSI rises above overbought.
"""

from typing import Any, Dict

import pandas as pd

from ..engine import SignalType, Side, Strategy, StrategyContext


class RSIMeanReversion(Strategy):
    """RSI-based mean reversion strategy.

    Parameters
    ----------
    rsi_period : int
        RSI lookback period (default: 14)
    oversold : float
        RSI level to buy (default: 30)
    overbought : float
        RSI level to sell (default: 70)
    use_short : bool
        Whether to short at overbought (default: False)
    """

    params = {
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70,
        "use_short": False,
    }

    def init(self, data: pd.DataFrame) -> None:
        close = data["Close"]
        period = self.params["rsi_period"]
        self.add_indicator("rsi", self.rsi(close, period))

    def next(self, row: pd.Series, indicators: Dict[str, float], ctx: StrategyContext) -> SignalType:
        rsi_val = indicators.get("rsi")
        if rsi_val is None or pd.isna(rsi_val):
            return SignalType.NONE

        oversold = self.params["oversold"]
        overbought = self.params["overbought"]
        has_position = ctx.position is not None

        if not has_position:
            if rsi_val < oversold:
                return SignalType.BUY
            elif rsi_val > overbought and self.params.get("use_short", False):
                return SignalType.SHORT
        else:
            if ctx.position.side == Side.LONG and rsi_val > overbought:
                return SignalType.SELL
            elif ctx.position.side == Side.SHORT and rsi_val < oversold:
                return SignalType.COVER

        return SignalType.NONE

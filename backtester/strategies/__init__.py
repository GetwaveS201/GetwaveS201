"""
Built-in example strategies.

Each strategy demonstrates a different approach and can serve as a template.
"""

from .sma_crossover import SMACrossover
from .rsi_mean_reversion import RSIMeanReversion
from .breakout import DonchianBreakout

__all__ = ["SMACrossover", "RSIMeanReversion", "DonchianBreakout"]

"""
Trading Strategies Module for Stock Trading Backtest System
Contains all 30 trading strategies as separate functions.

Each strategy function returns:
- entry_signal: Boolean Series indicating entry points
- exit_signal: Boolean Series indicating exit points
- stop_loss: Series with stop loss prices (or None for default)
- take_profit: Series with take profit prices (or None for default)
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Callable
from dataclasses import dataclass

from indicators import TechnicalIndicators as ti, add_all_indicators


@dataclass
class StrategySignal:
    """Container for strategy signals."""
    entry: pd.Series  # Boolean entry signals
    exit: pd.Series  # Boolean exit signals
    stop_loss: Optional[pd.Series] = None  # Stop loss prices
    take_profit: Optional[pd.Series] = None  # Take profit prices
    direction: str = 'long'  # 'long' or 'short'


class TradingStrategies:
    """
    Collection of 30 trading strategies for backtesting.
    All strategies are implemented as static methods.
    """

    # =============================================
    # MEAN REVERSION STRATEGIES (1-6)
    # =============================================

    @staticmethod
    def strategy_01_rsi_oversold(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 1: RSI Oversold Bounce
        Entry: RSI drops below 30
        Exit: RSI rises above 50

        Rationale: Oversold conditions often lead to price bounces.
        """
        params = params or {'entry_threshold': 30, 'exit_threshold': 50, 'period': 14}

        rsi = ti.rsi(df['close'], params['period'])

        entry = (rsi < params['entry_threshold']) & (rsi.shift(1) >= params['entry_threshold'])
        exit_signal = (rsi > params['exit_threshold']) & (rsi.shift(1) <= params['exit_threshold'])

        # Stop loss: 2 ATR below entry
        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 2 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_02_bollinger_snapback(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 2: Bollinger Band Snapback
        Entry: Close below lower band, then closes back inside
        Exit: Close reaches middle band or upper band

        Rationale: Price tends to revert to the mean after extreme moves.
        """
        params = params or {'period': 20, 'std_dev': 2.0}

        upper, middle, lower = ti.bollinger_bands(df['close'], params['period'], params['std_dev'])

        # Entry: was below lower band, now back inside
        below_lower = df['close'].shift(1) < lower.shift(1)
        back_inside = df['close'] > lower
        entry = below_lower & back_inside

        # Exit: reaches middle band
        exit_signal = (df['close'] >= middle) & (df['close'].shift(1) < middle.shift(1))

        stop_loss = lower - ti.atr(df, 14)
        take_profit = upper

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss, take_profit=take_profit)

    @staticmethod
    def strategy_03_zscore_reversion(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 3: Z-Score Reversion
        Entry: Price 2+ standard deviations below 20-day mean
        Exit: Price returns to within 0.5 std dev of mean

        Rationale: Extreme statistical deviations tend to revert.
        """
        params = params or {'period': 20, 'entry_zscore': -2.0, 'exit_zscore': -0.5}

        zscore = ti.zscore(df['close'], params['period'])

        entry = (zscore < params['entry_zscore']) & (zscore.shift(1) >= params['entry_zscore'])
        exit_signal = (zscore > params['exit_zscore']) & (zscore.shift(1) <= params['exit_zscore'])

        # Stop: if z-score goes even more extreme
        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 1.5 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_04_gap_fade(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 4: Gap Fade
        Entry: Gap down >3% on high volume, reversal entry when price rises
        Exit: Close gap (return to previous close) or end of day

        Rationale: Large gaps often fill during the trading day.
        """
        params = params or {'gap_pct': -3.0, 'volume_mult': 1.5}

        gap = (df['open'] - df['close'].shift(1)) / df['close'].shift(1) * 100
        volume_ratio = df['volume'] / df['volume'].rolling(20).mean()

        # Large gap down with elevated volume
        gap_down = gap < params['gap_pct']
        high_volume = volume_ratio > params['volume_mult']

        # Entry: gap down condition met, and price starts to recover
        price_recovering = df['close'] > df['open']
        entry = gap_down & high_volume & price_recovering

        # Exit: gap filled (price reaches previous close) or next day
        prev_close = df['close'].shift(1)
        exit_signal = df['high'] >= prev_close

        stop_loss = df['low'] - ti.atr(df, 14)
        take_profit = prev_close

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss, take_profit=take_profit)

    @staticmethod
    def strategy_05_williams_r_reversal(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 5: Williams %R Extreme Reversals
        Entry: Williams %R crosses from <-80 to >-80
        Exit: Williams %R crosses above -20

        Rationale: Extreme oversold followed by momentum shift signals reversal.
        """
        params = params or {'period': 14, 'oversold': -80, 'exit_level': -20}

        wr = ti.williams_r(df, params['period'])

        # Entry: was extremely oversold, now recovering
        was_oversold = wr.shift(1) < params['oversold']
        recovering = wr > params['oversold']
        entry = was_oversold & recovering

        # Exit: overbought
        exit_signal = (wr > params['exit_level']) & (wr.shift(1) <= params['exit_level'])

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 1.5 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_06_cci_reversal(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 6: CCI Extreme Reversals
        Entry: CCI crosses from <-100 to >-100
        Exit: CCI crosses above 0

        Rationale: CCI below -100 indicates oversold, crossing back signals reversal.
        """
        params = params or {'period': 20, 'oversold': -100, 'exit_level': 0}

        cci = ti.cci(df, params['period'])

        was_oversold = cci.shift(1) < params['oversold']
        recovering = cci > params['oversold']
        entry = was_oversold & recovering

        exit_signal = (cci > params['exit_level']) & (cci.shift(1) <= params['exit_level'])

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 1.5 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    # =============================================
    # MOMENTUM & TREND STRATEGIES (7-14)
    # =============================================

    @staticmethod
    def strategy_07_ema_crossover(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 7: EMA Crossover 20/50 with Volume Confirmation
        Entry: EMA 20 crosses above EMA 50 with above-average volume
        Exit: EMA 20 crosses below EMA 50

        Rationale: Moving average crossovers identify trend changes.
        """
        params = params or {'fast': 20, 'slow': 50, 'volume_mult': 1.2}

        ema_fast = ti.ema(df['close'], params['fast'])
        ema_slow = ti.ema(df['close'], params['slow'])
        volume_ratio = df['volume'] / df['volume'].rolling(20).mean()

        # Bullish crossover with volume
        crossover = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        volume_confirm = volume_ratio > params['volume_mult']
        entry = crossover & volume_confirm

        # Bearish crossover
        exit_signal = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))

        atr = ti.atr(df, 14)
        stop_loss = ema_slow - atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_08_macd_bullish(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 8: MACD Bullish Cross + Histogram Positive
        Entry: MACD line crosses above signal line AND histogram turns positive
        Exit: MACD histogram turns negative

        Rationale: MACD crossover with momentum confirmation is a strong signal.
        """
        params = params or {'fast': 12, 'slow': 26, 'signal': 9}

        macd_line, signal_line, histogram = ti.macd(df['close'], params['fast'], params['slow'], params['signal'])

        # Bullish cross and histogram positive
        macd_cross_up = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        histogram_positive = histogram > 0
        entry = macd_cross_up & histogram_positive

        # Exit: histogram turns negative
        exit_signal = (histogram < 0) & (histogram.shift(1) >= 0)

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 2 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_09_adx_trend(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 9: ADX Trend Strength
        Entry: ADX > 25 AND +DI > -DI (strong uptrend)
        Exit: +DI crosses below -DI OR ADX < 20

        Rationale: ADX measures trend strength; trade in direction of strong trends.
        """
        params = params or {'adx_threshold': 25, 'adx_exit': 20}

        adx, plus_di, minus_di = ti.adx(df, 14)

        # Strong uptrend
        strong_trend = adx > params['adx_threshold']
        bullish_di = plus_di > minus_di
        di_cross_up = (plus_di > minus_di) & (plus_di.shift(1) <= minus_di.shift(1))
        entry = strong_trend & bullish_di & di_cross_up

        # Exit: DI cross down or trend weakens
        di_cross_down = (plus_di < minus_di) & (plus_di.shift(1) >= minus_di.shift(1))
        weak_trend = adx < params['adx_exit']
        exit_signal = di_cross_down | weak_trend

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 1.5 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_10_supertrend(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 10: Supertrend Indicator Signals
        Entry: Supertrend flips to bullish (direction changes from -1 to 1)
        Exit: Supertrend flips to bearish

        Rationale: Supertrend is a trend-following indicator with built-in stop.
        """
        params = params or {'period': 10, 'multiplier': 3.0}

        supertrend, direction = ti.supertrend(df, params['period'], params['multiplier'])

        # Entry: direction changes to bullish
        entry = (direction == 1) & (direction.shift(1) == -1)

        # Exit: direction changes to bearish
        exit_signal = (direction == -1) & (direction.shift(1) == 1)

        # Supertrend line acts as trailing stop
        stop_loss = supertrend

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_11_donchian_breakout(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 11: Donchian Channel Breakouts
        Entry: Close breaks above 20-day high
        Exit: Close breaks below 10-day low (tighter exit)

        Rationale: Breakouts to new highs often lead to continued momentum.
        """
        params = params or {'entry_period': 20, 'exit_period': 10}

        upper, _, _ = ti.donchian_channel(df, params['entry_period'])
        _, _, lower_exit = ti.donchian_channel(df, params['exit_period'])

        # Breakout above upper channel
        entry = (df['close'] > upper.shift(1)) & (df['close'].shift(1) <= upper.shift(2))

        # Exit on break below lower channel
        exit_signal = df['close'] < lower_exit

        stop_loss = lower_exit

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_12_52week_high(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 12: 52-Week High Breakout with 2x Volume
        Entry: New 52-week high with at least 2x average volume
        Exit: 20% trailing stop or 10-day low break

        Rationale: New highs with volume conviction tend to continue.
        """
        params = params or {'lookback': 252, 'volume_mult': 2.0}

        high_52w = df['high'].rolling(params['lookback']).max()
        volume_ratio = df['volume'] / df['volume'].rolling(20).mean()

        # New 52-week high with volume
        new_high = df['high'] >= high_52w
        high_volume = volume_ratio >= params['volume_mult']
        entry = new_high & high_volume

        # Exit: price drops 20% from peak or breaks 10-day low
        _, _, lower_10 = ti.donchian_channel(df, 10)
        exit_signal = df['close'] < lower_10

        stop_loss = lower_10

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_13_triple_ema(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 13: Triple EMA Alignment
        Entry: EMA 9 > EMA 21 > EMA 55 (all aligned bullish)
        Exit: EMA 9 crosses below EMA 21

        Rationale: Multiple timeframe alignment confirms trend direction.
        """
        params = params or {'fast': 9, 'medium': 21, 'slow': 55}

        ema_fast = ti.ema(df['close'], params['fast'])
        ema_medium = ti.ema(df['close'], params['medium'])
        ema_slow = ti.ema(df['close'], params['slow'])

        # All EMAs aligned bullish
        aligned = (ema_fast > ema_medium) & (ema_medium > ema_slow)
        # Entry when alignment just occurred
        aligned_prev = (ema_fast.shift(1) > ema_medium.shift(1)) & (ema_medium.shift(1) > ema_slow.shift(1))
        entry = aligned & ~aligned_prev

        # Exit: fast crosses below medium
        exit_signal = (ema_fast < ema_medium) & (ema_fast.shift(1) >= ema_medium.shift(1))

        stop_loss = ema_slow - ti.atr(df, 14)

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_14_roc_momentum(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 14: Rate of Change Momentum
        Entry: ROC > 10% over 10 days
        Exit: ROC turns negative or < 2%

        Rationale: Strong momentum tends to persist in the short term.
        """
        params = params or {'period': 10, 'entry_threshold': 10, 'exit_threshold': 2}

        roc = ti.roc(df['close'], params['period'])

        # Strong momentum entry
        entry = (roc > params['entry_threshold']) & (roc.shift(1) <= params['entry_threshold'])

        # Exit: momentum fades
        exit_signal = (roc < params['exit_threshold']) & (roc.shift(1) >= params['exit_threshold'])

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 2 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    # =============================================
    # BREAKOUT & VOLATILITY STRATEGIES (15-20)
    # =============================================

    @staticmethod
    def strategy_15_consolidation_breakout(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 15: Consolidation Breakout
        Entry: 5+ day narrow range (<5% ATR), then break out
        Exit: Return to consolidation range or opposite breakout

        Rationale: Tight ranges precede explosive moves.
        """
        params = params or {'period': 5, 'atr_mult': 0.05, 'breakout_mult': 1.0}

        atr = ti.atr(df, 14)

        # Check for consolidation (narrow range over period)
        period_range = df['high'].rolling(params['period']).max() - df['low'].rolling(params['period']).min()
        consolidating = period_range < (params['atr_mult'] * df['close'] * params['period'])

        # Breakout: price moves beyond consolidation range
        consolidation_high = df['high'].rolling(params['period']).max()
        breakout = df['close'] > consolidation_high.shift(1)
        entry = consolidating.shift(1) & breakout

        # Exit: return to range or 2 ATR trailing stop
        exit_signal = df['close'] < (df['close'].rolling(10).max() - 2 * atr)

        stop_loss = df['low'].rolling(params['period']).min()

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_16_volume_breakout(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 16: Volume Breakout
        Entry: 3x average volume + price up >2%
        Exit: Volume returns to normal with price stalling

        Rationale: High volume price increases indicate institutional interest.
        """
        params = params or {'volume_mult': 3.0, 'price_pct': 2.0}

        volume_ratio = df['volume'] / df['volume'].rolling(20).mean()
        daily_return = (df['close'] - df['open']) / df['open'] * 100

        # High volume + strong price move
        high_volume = volume_ratio >= params['volume_mult']
        price_up = daily_return >= params['price_pct']
        entry = high_volume & price_up

        # Exit: volume normalizes and price stalls
        volume_normal = volume_ratio < 1.5
        price_flat = abs(daily_return) < 1
        exit_signal = volume_normal & price_flat

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 1.5 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_17_atr_expansion(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 17: ATR Expansion
        Entry: ATR increases 50%+ in 3 days (volatility expansion)
        Exit: ATR contracts or price reverses

        Rationale: Volatility expansion often precedes trend moves.
        """
        params = params or {'expansion_pct': 50, 'period': 3}

        atr = ti.atr(df, 14)
        atr_change = (atr - atr.shift(params['period'])) / atr.shift(params['period']) * 100

        # Volatility expansion with bullish price action
        expanding = atr_change > params['expansion_pct']
        bullish = df['close'] > df['close'].shift(params['period'])
        entry = expanding & bullish

        # Exit: volatility contracts or trend reverses
        contracting = atr < atr.shift(1)
        price_falling = df['close'] < df['close'].shift(3)
        exit_signal = contracting & price_falling

        stop_loss = df['close'] - 2 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_18_bollinger_squeeze(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 18: Bollinger Band Squeeze
        Entry: Bandwidth at lowest in 20 days, then expands upward
        Exit: Bandwidth contracts again or price breaks lower band

        Rationale: Low volatility periods precede explosive moves.
        """
        params = params or {'period': 20, 'std_dev': 2.0}

        bandwidth = ti.bollinger_bandwidth(df['close'], params['period'], params['std_dev'])
        upper, middle, lower = ti.bollinger_bands(df['close'], params['period'], params['std_dev'])

        # Squeeze: bandwidth at 20-day low
        squeeze = bandwidth == bandwidth.rolling(params['period']).min()

        # Breakout: squeeze yesterday, expanding today with bullish close
        expanding = bandwidth > bandwidth.shift(1)
        bullish = df['close'] > middle
        entry = squeeze.shift(1) & expanding & bullish

        # Exit: close below middle band
        exit_signal = df['close'] < middle

        stop_loss = lower

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_19_opening_range_breakout(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 19: Opening Range Breakout
        Entry: Break above/below opening range (approximated with daily open)
        Exit: End of day or stop hit

        Note: Using daily data, we approximate with open vs previous close.

        Rationale: Early range breakouts often set the day's direction.
        """
        params = params or {'range_mult': 0.5}

        atr = ti.atr(df, 14)

        # Approximate opening range using ATR
        opening_range_high = df['open'] + (params['range_mult'] * atr)
        opening_range_low = df['open'] - (params['range_mult'] * atr)

        # Breakout above opening range
        entry = df['high'] > opening_range_high

        # Exit at close or if price breaks low
        exit_signal = df['low'] < opening_range_low

        stop_loss = opening_range_low

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_20_pivot_breakout(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 20: Pivot Point R1/R2 Breakouts
        Entry: Close above R1 or R2
        Exit: Close below pivot point

        Rationale: Pivot breakouts indicate strong bullish momentum.
        """
        params = params or {'level': 'r1'}  # 'r1' or 'r2'

        pivot, r1, r2, s1, s2 = ti.pivot_points(df)

        if params['level'] == 'r2':
            entry = (df['close'] > r2) & (df['close'].shift(1) <= r2.shift(1))
            stop_loss = r1
        else:  # r1
            entry = (df['close'] > r1) & (df['close'].shift(1) <= r1.shift(1))
            stop_loss = pivot

        # Exit below pivot
        exit_signal = df['close'] < pivot

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    # =============================================
    # MARKET STRUCTURE STRATEGIES (21-25)
    # =============================================

    @staticmethod
    def strategy_21_higher_highs_lows(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 21: Higher Highs + Higher Lows Continuation
        Entry: 3+ consecutive higher highs AND higher lows
        Exit: Lower low formed

        Rationale: Established uptrend structure tends to continue.
        """
        params = params or {'periods': 3}

        hh = ti.higher_high(df, params['periods'])
        hl = ti.higher_low(df, params['periods'])

        # Both conditions met
        entry = hh & hl & ~(hh.shift(1) & hl.shift(1))

        # Lower low breaks structure
        ll = ti.lower_low(df, 2)
        exit_signal = ll

        atr = ti.atr(df, 14)
        stop_loss = df['low'].rolling(params['periods']).min() - atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_22_support_bounce(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 22: Support/Resistance Bounce
        Entry: Price within 2% of tested support level, then bounces
        Exit: Break below support or reach resistance

        Rationale: Established support levels often hold.
        """
        params = params or {'lookback': 20, 'proximity_pct': 2.0}

        # Use recent lows as support
        support = df['low'].rolling(params['lookback']).min()
        proximity = (df['low'] - support) / support * 100

        # Near support and bouncing
        near_support = proximity < params['proximity_pct']
        bouncing = df['close'] > df['open']  # Green candle
        entry = near_support & bouncing

        # Exit: break below support
        exit_signal = df['close'] < support

        stop_loss = support - ti.atr(df, 14)
        take_profit = df['high'].rolling(params['lookback']).max()  # Resistance

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss, take_profit=take_profit)

    @staticmethod
    def strategy_23_fibonacci_retracement(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 23: Fibonacci Retracement Entries
        Entry: Price bounces from 38.2%, 50%, or 61.8% retracement
        Exit: New high or break below 78.6%

        Rationale: Key Fibonacci levels act as support in uptrends.
        """
        params = params or {'lookback': 50, 'fib_level': 0.618}

        # Calculate swing high and low
        swing_high = df['high'].rolling(params['lookback']).max()
        swing_low = df['low'].rolling(params['lookback']).min()

        # Fibonacci retracement level
        fib_range = swing_high - swing_low
        fib_level = swing_high - (params['fib_level'] * fib_range)

        # Near Fibonacci level and bouncing
        near_fib = abs(df['low'] - fib_level) / fib_level < 0.02
        bouncing = df['close'] > df['open']
        entry = near_fib & bouncing

        # Exit: break below deeper retracement
        deeper_fib = swing_high - (0.786 * fib_range)
        exit_signal = df['close'] < deeper_fib

        stop_loss = deeper_fib
        take_profit = swing_high

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss, take_profit=take_profit)

    @staticmethod
    def strategy_24_trendline_retest(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 24: Trendline Retest Entries
        Entry: Price retests upward sloping trendline (approximated)
        Exit: Trendline break

        Note: Simplified using EMA as trendline proxy.

        Rationale: Trendline retests offer low-risk entry points.
        """
        params = params or {'ema_period': 20, 'proximity_pct': 1.0}

        ema = ti.ema(df['close'], params['ema_period'])
        proximity = (df['low'] - ema) / ema * 100

        # Near EMA (trendline proxy) in uptrend
        near_trendline = (proximity > -params['proximity_pct']) & (proximity < params['proximity_pct'])
        uptrend = ema > ema.shift(5)  # EMA rising
        bouncing = df['close'] > ema
        entry = near_trendline & uptrend & bouncing

        # Exit: close below EMA
        exit_signal = (df['close'] < ema) & (df['close'].shift(1) >= ema.shift(1))

        stop_loss = ema - ti.atr(df, 14)

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_25_inside_bar_breakout(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 25: Inside Bar Breakout Next Day
        Entry: Inside bar forms, buy on break above mother bar high
        Exit: Break below inside bar low

        Rationale: Inside bars represent consolidation before expansion.
        """
        params = params or {}

        inside = ti.inside_bar(df)

        # Mother bar high (previous bar)
        mother_high = df['high'].shift(1)
        mother_low = df['low'].shift(1)

        # Entry: inside bar yesterday, break above mother bar today
        entry = inside.shift(1) & (df['high'] > mother_high.shift(1))

        # Exit: break below inside bar low
        inside_low = df['low'].where(inside).shift(1).ffill()
        exit_signal = df['close'] < inside_low

        stop_loss = mother_low.shift(1)

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    # =============================================
    # VOLUME & MONEY FLOW STRATEGIES (26-30)
    # =============================================

    @staticmethod
    def strategy_26_obv_divergence(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 26: OBV Divergence
        Entry: Price makes lower low, OBV makes higher low (bullish divergence)
        Exit: OBV breaks down

        Rationale: Volume precedes price; divergence signals potential reversal.
        """
        params = params or {'lookback': 10}

        obv = ti.obv_fast(df)

        # Price lower low
        price_ll = df['low'] < df['low'].rolling(params['lookback']).min().shift(1)

        # OBV higher low (compare current to lookback period min)
        obv_min_prev = obv.rolling(params['lookback']).min().shift(1)
        obv_hl = obv > obv_min_prev

        # Bullish divergence
        entry = price_ll & obv_hl

        # Exit: OBV breaks down (below 10-day min)
        exit_signal = obv < obv.rolling(params['lookback']).min().shift(1)

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 2 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_27_mfi_reversal(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 27: Money Flow Index Reversal
        Entry: MFI crosses from <20 to >40
        Exit: MFI > 80 or crosses back below 50

        Rationale: MFI oversold to overbought signals strong buying.
        """
        params = params or {'oversold': 20, 'entry_confirm': 40, 'overbought': 80, 'exit_level': 50}

        mfi = ti.mfi(df, 14)

        # Was oversold, now recovering strongly
        was_oversold = mfi.rolling(5).min() < params['oversold']
        recovering = (mfi > params['entry_confirm']) & (mfi.shift(1) <= params['entry_confirm'])
        entry = was_oversold & recovering

        # Exit: overbought or momentum fading
        overbought = mfi > params['overbought']
        fading = (mfi < params['exit_level']) & (mfi.shift(1) >= params['exit_level'])
        exit_signal = overbought | fading

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 1.5 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_28_cmf_cross(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 28: Chaikin Money Flow Bullish Cross
        Entry: CMF crosses above 0
        Exit: CMF crosses below 0

        Rationale: CMF above 0 indicates buying pressure.
        """
        params = params or {'period': 20}

        cmf = ti.chaikin_money_flow(df, params['period'])

        # Bullish cross
        entry = (cmf > 0) & (cmf.shift(1) <= 0)

        # Bearish cross
        exit_signal = (cmf < 0) & (cmf.shift(1) >= 0)

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 1.5 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)

    @staticmethod
    def strategy_29_vwap_reversion(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 29: VWAP Mean Reversion
        Entry: Price >3% below VWAP, showing signs of reversal
        Exit: Price returns to VWAP

        Rationale: Price tends to revert to VWAP.
        """
        params = params or {'deviation_pct': 3.0, 'period': 20}

        vwap = ti.vwap(df, params['period'])
        deviation = (df['close'] - vwap) / vwap * 100

        # Below VWAP and recovering
        below_vwap = deviation < -params['deviation_pct']
        recovering = df['close'] > df['close'].shift(1)
        entry = below_vwap & recovering

        # Exit: return to VWAP
        exit_signal = (deviation > 0) & (deviation.shift(1) <= 0)

        stop_loss = df['low'].rolling(5).min()
        take_profit = vwap

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss, take_profit=take_profit)

    @staticmethod
    def strategy_30_volume_spike_breakout(df: pd.DataFrame, params: dict = None) -> StrategySignal:
        """
        Strategy 30: Unusual Volume Spike + Price Breakout
        Entry: 5x average volume with price breakout above recent high
        Exit: Volume normalizes with price stagnation

        Rationale: Unusual volume indicates institutional activity.
        """
        params = params or {'volume_mult': 5.0, 'lookback': 10}

        volume_ratio = df['volume'] / df['volume'].rolling(20).mean()
        recent_high = df['high'].rolling(params['lookback']).max().shift(1)

        # Volume spike with price breakout
        volume_spike = volume_ratio >= params['volume_mult']
        breakout = df['close'] > recent_high
        entry = volume_spike & breakout

        # Exit: volume and momentum fade
        volume_normal = volume_ratio < 2
        no_progress = df['close'] < df['close'].shift(3)
        exit_signal = volume_normal & no_progress

        atr = ti.atr(df, 14)
        stop_loss = df['close'] - 2 * atr

        return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)


# =============================================
# STRATEGY REGISTRY
# =============================================

STRATEGY_REGISTRY: Dict[str, Tuple[Callable, str, str]] = {
    'rsi_oversold': (TradingStrategies.strategy_01_rsi_oversold, 'Mean Reversion', 'RSI Oversold Bounce'),
    'bollinger_snapback': (TradingStrategies.strategy_02_bollinger_snapback, 'Mean Reversion', 'Bollinger Band Snapback'),
    'zscore_reversion': (TradingStrategies.strategy_03_zscore_reversion, 'Mean Reversion', 'Z-Score Reversion'),
    'gap_fade': (TradingStrategies.strategy_04_gap_fade, 'Mean Reversion', 'Gap Fade'),
    'williams_r_reversal': (TradingStrategies.strategy_05_williams_r_reversal, 'Mean Reversion', 'Williams %R Extreme Reversal'),
    'cci_reversal': (TradingStrategies.strategy_06_cci_reversal, 'Mean Reversion', 'CCI Extreme Reversal'),
    'ema_crossover': (TradingStrategies.strategy_07_ema_crossover, 'Momentum', 'EMA 20/50 Crossover'),
    'macd_bullish': (TradingStrategies.strategy_08_macd_bullish, 'Momentum', 'MACD Bullish Cross'),
    'adx_trend': (TradingStrategies.strategy_09_adx_trend, 'Trend', 'ADX Trend Strength'),
    'supertrend': (TradingStrategies.strategy_10_supertrend, 'Trend', 'Supertrend'),
    'donchian_breakout': (TradingStrategies.strategy_11_donchian_breakout, 'Breakout', 'Donchian Channel Breakout'),
    '52week_high': (TradingStrategies.strategy_12_52week_high, 'Breakout', '52-Week High Breakout'),
    'triple_ema': (TradingStrategies.strategy_13_triple_ema, 'Trend', 'Triple EMA Alignment'),
    'roc_momentum': (TradingStrategies.strategy_14_roc_momentum, 'Momentum', 'Rate of Change Momentum'),
    'consolidation_breakout': (TradingStrategies.strategy_15_consolidation_breakout, 'Breakout', 'Consolidation Breakout'),
    'volume_breakout': (TradingStrategies.strategy_16_volume_breakout, 'Breakout', 'Volume Breakout'),
    'atr_expansion': (TradingStrategies.strategy_17_atr_expansion, 'Volatility', 'ATR Expansion'),
    'bollinger_squeeze': (TradingStrategies.strategy_18_bollinger_squeeze, 'Volatility', 'Bollinger Band Squeeze'),
    'opening_range': (TradingStrategies.strategy_19_opening_range_breakout, 'Breakout', 'Opening Range Breakout'),
    'pivot_breakout': (TradingStrategies.strategy_20_pivot_breakout, 'Breakout', 'Pivot Point Breakout'),
    'higher_highs_lows': (TradingStrategies.strategy_21_higher_highs_lows, 'Structure', 'Higher Highs/Lows'),
    'support_bounce': (TradingStrategies.strategy_22_support_bounce, 'Structure', 'Support Bounce'),
    'fibonacci_retracement': (TradingStrategies.strategy_23_fibonacci_retracement, 'Structure', 'Fibonacci Retracement'),
    'trendline_retest': (TradingStrategies.strategy_24_trendline_retest, 'Structure', 'Trendline Retest'),
    'inside_bar': (TradingStrategies.strategy_25_inside_bar_breakout, 'Structure', 'Inside Bar Breakout'),
    'obv_divergence': (TradingStrategies.strategy_26_obv_divergence, 'Volume', 'OBV Divergence'),
    'mfi_reversal': (TradingStrategies.strategy_27_mfi_reversal, 'Volume', 'MFI Reversal'),
    'cmf_cross': (TradingStrategies.strategy_28_cmf_cross, 'Volume', 'Chaikin Money Flow Cross'),
    'vwap_reversion': (TradingStrategies.strategy_29_vwap_reversion, 'Volume', 'VWAP Mean Reversion'),
    'volume_spike': (TradingStrategies.strategy_30_volume_spike_breakout, 'Volume', 'Volume Spike Breakout'),
}


def get_all_strategies() -> Dict[str, Tuple[Callable, str, str]]:
    """Return the complete strategy registry."""
    return STRATEGY_REGISTRY


def get_strategy(name: str) -> Tuple[Callable, str, str]:
    """Get a specific strategy by name."""
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[name]


def list_strategies() -> None:
    """Print all available strategies."""
    print("\nAvailable Trading Strategies:")
    print("=" * 70)
    for i, (name, (func, category, description)) in enumerate(STRATEGY_REGISTRY.items(), 1):
        print(f"{i:2}. [{category:15}] {name:25} - {description}")


if __name__ == '__main__':
    # Test strategies with sample data
    import yfinance as yf

    print("Testing Trading Strategies...")
    print("-" * 50)

    # Download sample data
    ticker = yf.Ticker('SPY')
    df = ticker.history(start='2020-01-01', end='2024-01-01')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    df.index = df.index.tz_localize(None)

    print(f"Loaded {len(df)} days of SPY data\n")

    # List all strategies
    list_strategies()

    # Test each strategy
    print("\n" + "=" * 70)
    print("Testing all strategies...")
    print("=" * 70)

    for name, (strategy_func, category, description) in STRATEGY_REGISTRY.items():
        try:
            signal = strategy_func(df)
            entry_count = signal.entry.sum()
            exit_count = signal.exit.sum()
            print(f"{name:25} - Entries: {entry_count:4}, Exits: {exit_count:4}")
        except Exception as e:
            print(f"{name:25} - ERROR: {str(e)[:40]}")

    print("\nAll strategy tests completed!")

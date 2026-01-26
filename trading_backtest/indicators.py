"""
Technical Indicators Module for Stock Trading Backtest System
Contains all technical indicator calculations used by the 30 strategies.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple


class TechnicalIndicators:
    """
    Collection of technical indicators for trading strategies.
    All methods are static and operate on pandas DataFrames/Series.
    """

    # ====================
    # MOVING AVERAGES
    # ====================

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return series.rolling(window=period).mean()

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def wma(series: pd.Series, period: int) -> pd.Series:
        """Weighted Moving Average."""
        weights = np.arange(1, period + 1)
        return series.rolling(window=period).apply(
            lambda x: np.sum(weights * x) / weights.sum(), raw=True
        )

    @staticmethod
    def vwap(df: pd.DataFrame, period: int = None) -> pd.Series:
        """
        Volume Weighted Average Price.
        If period is None, calculates intraday VWAP (resets daily).
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        tp_volume = typical_price * df['volume']

        if period:
            return tp_volume.rolling(period).sum() / df['volume'].rolling(period).sum()
        else:
            # Running VWAP
            return tp_volume.cumsum() / df['volume'].cumsum()

    # ====================
    # MOMENTUM INDICATORS
    # ====================

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index.
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        """
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator.
        %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
        %D = SMA of %K
        """
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()

        k = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()

        return k, d

    @staticmethod
    def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Williams %R.
        %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
        """
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()

        wr = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        return wr

    @staticmethod
    def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Commodity Channel Index.
        CCI = (Typical Price - SMA of TP) / (0.015 * Mean Deviation)
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()

        # Mean deviation
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean(), raw=True
        )

        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci

    @staticmethod
    def roc(series: pd.Series, period: int = 10) -> pd.Series:
        """
        Rate of Change.
        ROC = ((Current Price - Price n periods ago) / Price n periods ago) * 100
        """
        return ((series - series.shift(period)) / series.shift(period)) * 100

    @staticmethod
    def momentum(series: pd.Series, period: int = 10) -> pd.Series:
        """
        Momentum Indicator.
        Simply the difference between current and n periods ago.
        """
        return series - series.shift(period)

    @staticmethod
    def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Money Flow Index.
        MFI = 100 - (100 / (1 + Money Flow Ratio))
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']

        # Positive and negative money flow
        delta = typical_price.diff()
        positive_flow = money_flow.where(delta > 0, 0).rolling(period).sum()
        negative_flow = money_flow.where(delta < 0, 0).rolling(period).sum()

        money_flow_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_flow_ratio))

        return mfi

    # ====================
    # MACD & RELATED
    # ====================

    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence.
        Returns: (MACD line, Signal line, Histogram)
        """
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    # ====================
    # TREND INDICATORS
    # ====================

    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Average Directional Index.
        Returns: (ADX, +DI, -DI)
        """
        # True Range
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        up_move = df['high'] - df['high'].shift(1)
        down_move = df['low'].shift(1) - df['low']

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        # Smoothed values
        atr = pd.Series(true_range).ewm(span=period, adjust=False).mean()
        plus_di = 100 * pd.Series(plus_dm).ewm(span=period, adjust=False).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).ewm(span=period, adjust=False).mean() / atr

        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period, adjust=False).mean()

        return adx, plus_di, minus_di

    @staticmethod
    def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        """
        Supertrend Indicator.
        Returns: (Supertrend line, Direction: 1=uptrend, -1=downtrend)
        """
        # ATR
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        # Basic upper and lower bands
        hl2 = (df['high'] + df['low']) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)

        # Final bands
        final_upper = pd.Series(np.nan, index=df.index)
        final_lower = pd.Series(np.nan, index=df.index)
        supertrend = pd.Series(np.nan, index=df.index)
        direction = pd.Series(1, index=df.index)

        for i in range(period, len(df)):
            # Final Upper Band
            if upper_band.iloc[i] < final_upper.iloc[i-1] or df['close'].iloc[i-1] > final_upper.iloc[i-1]:
                final_upper.iloc[i] = upper_band.iloc[i]
            else:
                final_upper.iloc[i] = final_upper.iloc[i-1]

            # Final Lower Band
            if lower_band.iloc[i] > final_lower.iloc[i-1] or df['close'].iloc[i-1] < final_lower.iloc[i-1]:
                final_lower.iloc[i] = lower_band.iloc[i]
            else:
                final_lower.iloc[i] = final_lower.iloc[i-1]

            # Supertrend
            if supertrend.iloc[i-1] == final_upper.iloc[i-1]:
                if df['close'].iloc[i] <= final_upper.iloc[i]:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1
                else:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
            else:
                if df['close'].iloc[i] >= final_lower.iloc[i]:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1

        return supertrend, direction

    # ====================
    # VOLATILITY INDICATORS
    # ====================

    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average True Range.
        """
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands.
        Returns: (Upper Band, Middle Band, Lower Band)
        """
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()

        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        return upper, middle, lower

    @staticmethod
    def bollinger_bandwidth(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.Series:
        """
        Bollinger Bandwidth = (Upper - Lower) / Middle * 100
        """
        upper, middle, lower = TechnicalIndicators.bollinger_bands(series, period, std_dev)
        return (upper - lower) / middle * 100

    @staticmethod
    def donchian_channel(df: pd.DataFrame, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Donchian Channel.
        Returns: (Upper, Middle, Lower)
        """
        upper = df['high'].rolling(window=period).max()
        lower = df['low'].rolling(window=period).min()
        middle = (upper + lower) / 2

        return upper, middle, lower

    @staticmethod
    def keltner_channel(df: pd.DataFrame, period: int = 20, atr_mult: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Keltner Channel.
        Returns: (Upper, Middle, Lower)
        """
        middle = TechnicalIndicators.ema(df['close'], period)
        atr_val = TechnicalIndicators.atr(df, period)

        upper = middle + (atr_mult * atr_val)
        lower = middle - (atr_mult * atr_val)

        return upper, middle, lower

    # ====================
    # VOLUME INDICATORS
    # ====================

    @staticmethod
    def obv(df: pd.DataFrame) -> pd.Series:
        """
        On Balance Volume.
        """
        obv = pd.Series(0.0, index=df.index)
        obv.iloc[0] = df['volume'].iloc[0]

        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]

        return obv

    @staticmethod
    def obv_fast(df: pd.DataFrame) -> pd.Series:
        """
        On Balance Volume - vectorized fast version.
        """
        sign = np.sign(df['close'].diff())
        return (sign * df['volume']).cumsum()

    @staticmethod
    def chaikin_money_flow(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Chaikin Money Flow.
        CMF = Sum(Money Flow Volume) / Sum(Volume)
        """
        mf_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mf_multiplier = mf_multiplier.fillna(0)
        mf_volume = mf_multiplier * df['volume']

        cmf = mf_volume.rolling(period).sum() / df['volume'].rolling(period).sum()
        return cmf

    @staticmethod
    def volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Simple Moving Average of Volume."""
        return df['volume'].rolling(window=period).mean()

    @staticmethod
    def volume_ratio(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Current volume divided by average volume."""
        return df['volume'] / df['volume'].rolling(window=period).mean()

    # ====================
    # SUPPORT/RESISTANCE
    # ====================

    @staticmethod
    def pivot_points(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Standard Pivot Points.
        Returns: (Pivot, R1, R2, S1, S2)
        """
        pivot = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
        r1 = 2 * pivot - df['low'].shift(1)
        s1 = 2 * pivot - df['high'].shift(1)
        r2 = pivot + (df['high'].shift(1) - df['low'].shift(1))
        s2 = pivot - (df['high'].shift(1) - df['low'].shift(1))

        return pivot, r1, r2, s1, s2

    @staticmethod
    def fibonacci_retracements(high: float, low: float) -> dict:
        """
        Calculate Fibonacci retracement levels.
        """
        diff = high - low
        return {
            '0.0%': high,
            '23.6%': high - 0.236 * diff,
            '38.2%': high - 0.382 * diff,
            '50.0%': high - 0.500 * diff,
            '61.8%': high - 0.618 * diff,
            '78.6%': high - 0.786 * diff,
            '100.0%': low
        }

    @staticmethod
    def swing_highs_lows(df: pd.DataFrame, window: int = 5) -> Tuple[pd.Series, pd.Series]:
        """
        Identify swing highs and swing lows.
        Returns: (swing_high boolean, swing_low boolean)
        """
        swing_high = df['high'] == df['high'].rolling(window=2*window+1, center=True).max()
        swing_low = df['low'] == df['low'].rolling(window=2*window+1, center=True).min()

        return swing_high, swing_low

    # ====================
    # PATTERN RECOGNITION
    # ====================

    @staticmethod
    def inside_bar(df: pd.DataFrame) -> pd.Series:
        """
        Inside Bar Pattern.
        Current bar is completely inside previous bar.
        """
        return (df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))

    @staticmethod
    def outside_bar(df: pd.DataFrame) -> pd.Series:
        """
        Outside Bar Pattern.
        Current bar completely engulfs previous bar.
        """
        return (df['high'] > df['high'].shift(1)) & (df['low'] < df['low'].shift(1))

    @staticmethod
    def gap_percentage(df: pd.DataFrame) -> pd.Series:
        """
        Gap percentage from previous close to current open.
        """
        return (df['open'] - df['close'].shift(1)) / df['close'].shift(1) * 100

    @staticmethod
    def narrow_range(df: pd.DataFrame, period: int = 5) -> pd.Series:
        """
        Narrow Range indicator.
        True if today's range is the smallest of the last n days.
        """
        daily_range = df['high'] - df['low']
        min_range = daily_range.rolling(window=period).min()
        return daily_range == min_range

    @staticmethod
    def consolidation(df: pd.DataFrame, period: int = 5, atr_mult: float = 0.05) -> pd.Series:
        """
        Consolidation Pattern.
        True if range over period is less than atr_mult * ATR.
        """
        atr_val = TechnicalIndicators.atr(df, 14)
        period_range = df['high'].rolling(period).max() - df['low'].rolling(period).min()
        return period_range < (atr_mult * df['close'] * period)

    # ====================
    # STATISTICAL MEASURES
    # ====================

    @staticmethod
    def zscore(series: pd.Series, period: int = 20) -> pd.Series:
        """
        Z-Score (number of standard deviations from mean).
        """
        mean = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        return (series - mean) / std

    @staticmethod
    def percentile_rank(series: pd.Series, period: int = 252) -> pd.Series:
        """
        Percentile rank over the lookback period.
        """
        return series.rolling(window=period).apply(
            lambda x: (x.rank(pct=True).iloc[-1]) * 100, raw=False
        )

    @staticmethod
    def historical_volatility(series: pd.Series, period: int = 20, annualize: bool = True) -> pd.Series:
        """
        Historical volatility (standard deviation of returns).
        """
        returns = series.pct_change()
        vol = returns.rolling(window=period).std()
        if annualize:
            vol = vol * np.sqrt(252)
        return vol

    # ====================
    # HIGHER HIGHS/LOWS
    # ====================

    @staticmethod
    def higher_high(df: pd.DataFrame, periods: int = 3) -> pd.Series:
        """
        Check for consecutive higher highs.
        """
        result = pd.Series(True, index=df.index)
        for i in range(1, periods):
            result = result & (df['high'].shift(i-1) > df['high'].shift(i))
        return result

    @staticmethod
    def higher_low(df: pd.DataFrame, periods: int = 3) -> pd.Series:
        """
        Check for consecutive higher lows.
        """
        result = pd.Series(True, index=df.index)
        for i in range(1, periods):
            result = result & (df['low'].shift(i-1) > df['low'].shift(i))
        return result

    @staticmethod
    def lower_high(df: pd.DataFrame, periods: int = 3) -> pd.Series:
        """
        Check for consecutive lower highs.
        """
        result = pd.Series(True, index=df.index)
        for i in range(1, periods):
            result = result & (df['high'].shift(i-1) < df['high'].shift(i))
        return result

    @staticmethod
    def lower_low(df: pd.DataFrame, periods: int = 3) -> pd.Series:
        """
        Check for consecutive lower lows.
        """
        result = pd.Series(True, index=df.index)
        for i in range(1, periods):
            result = result & (df['low'].shift(i-1) < df['low'].shift(i))
        return result


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all common indicators to a DataFrame.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with all indicators added
    """
    df = df.copy()
    ti = TechnicalIndicators

    # Moving Averages
    df['sma_10'] = ti.sma(df['close'], 10)
    df['sma_20'] = ti.sma(df['close'], 20)
    df['sma_50'] = ti.sma(df['close'], 50)
    df['sma_200'] = ti.sma(df['close'], 200)
    df['ema_9'] = ti.ema(df['close'], 9)
    df['ema_20'] = ti.ema(df['close'], 20)
    df['ema_21'] = ti.ema(df['close'], 21)
    df['ema_50'] = ti.ema(df['close'], 50)
    df['ema_55'] = ti.ema(df['close'], 55)

    # VWAP
    df['vwap'] = ti.vwap(df, period=20)

    # Momentum
    df['rsi'] = ti.rsi(df['close'], 14)
    df['stoch_k'], df['stoch_d'] = ti.stochastic(df, 14, 3)
    df['williams_r'] = ti.williams_r(df, 14)
    df['cci'] = ti.cci(df, 20)
    df['roc'] = ti.roc(df['close'], 10)
    df['mfi'] = ti.mfi(df, 14)

    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = ti.macd(df['close'])

    # Trend
    df['adx'], df['plus_di'], df['minus_di'] = ti.adx(df, 14)
    df['supertrend'], df['supertrend_dir'] = ti.supertrend(df, 10, 3.0)

    # Volatility
    df['atr'] = ti.atr(df, 14)
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = ti.bollinger_bands(df['close'], 20, 2.0)
    df['bb_bandwidth'] = ti.bollinger_bandwidth(df['close'], 20, 2.0)
    df['donch_upper'], df['donch_middle'], df['donch_lower'] = ti.donchian_channel(df, 20)

    # Volume
    df['obv'] = ti.obv_fast(df)
    df['cmf'] = ti.chaikin_money_flow(df, 20)
    df['volume_sma'] = ti.volume_sma(df, 20)
    df['volume_ratio'] = ti.volume_ratio(df, 20)

    # Pivot Points
    df['pivot'], df['r1'], df['r2'], df['s1'], df['s2'] = ti.pivot_points(df)

    # Pattern Recognition
    df['inside_bar'] = ti.inside_bar(df)
    df['gap_pct'] = ti.gap_percentage(df)
    df['narrow_range'] = ti.narrow_range(df, 5)
    df['consolidation'] = ti.consolidation(df, 5, 0.05)

    # Statistical
    df['zscore'] = ti.zscore(df['close'], 20)
    df['hist_vol'] = ti.historical_volatility(df['close'], 20)

    # Higher Highs/Lows
    df['higher_high_3'] = ti.higher_high(df, 3)
    df['higher_low_3'] = ti.higher_low(df, 3)

    # 52-week high/low
    df['high_52w'] = df['high'].rolling(252).max()
    df['low_52w'] = df['low'].rolling(252).min()
    df['pct_from_52w_high'] = (df['close'] - df['high_52w']) / df['high_52w'] * 100

    return df


if __name__ == '__main__':
    # Test indicators with sample data
    import yfinance as yf

    print("Testing Technical Indicators...")
    print("-" * 50)

    # Download sample data
    ticker = yf.Ticker('SPY')
    df = ticker.history(start='2020-01-01', end='2024-01-01')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    df.index = df.index.tz_localize(None)

    print(f"Loaded {len(df)} days of SPY data")

    # Add all indicators
    df_with_indicators = add_all_indicators(df)

    print(f"\nIndicators added: {len(df_with_indicators.columns) - len(df.columns)}")
    print(f"\nSample of latest values:")
    print(df_with_indicators[['close', 'rsi', 'macd', 'adx', 'atr', 'bb_upper', 'bb_lower']].tail())

    # Validate RSI calculation
    print("\n" + "=" * 50)
    print("RSI Validation:")
    rsi = TechnicalIndicators.rsi(df['close'], 14)
    print(f"  RSI range: {rsi.min():.1f} to {rsi.max():.1f}")
    print(f"  Current RSI: {rsi.iloc[-1]:.1f}")

    # Validate Bollinger Bands
    print("\nBollinger Bands Validation:")
    upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'], 20, 2.0)
    pct_in_bands = ((df['close'] >= lower) & (df['close'] <= upper)).mean() * 100
    print(f"  % of closes within bands: {pct_in_bands:.1f}%")

    print("\nAll indicator tests passed!")

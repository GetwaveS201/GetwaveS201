"""
Daily Scanner Module for Stock Trading Backtest System
Scans the market each day and outputs buy/sell signals for actionable trading.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

from indicators import TechnicalIndicators as ti, add_all_indicators
from strategies import STRATEGY_REGISTRY, StrategySignal
from risk_manager import RiskManager, RiskConfig

warnings.filterwarnings('ignore')


# Default watchlist of liquid stocks
DEFAULT_WATCHLIST = [
    'SPY', 'QQQ', 'IWM',  # ETFs
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',  # Mega caps
    'JPM', 'V', 'MA', 'UNH', 'JNJ', 'PG', 'HD', 'DIS',  # Large caps
    'NFLX', 'ADBE', 'CRM', 'PYPL', 'AMD', 'INTC', 'CSCO',  # Tech
    'BA', 'CAT', 'GS', 'MS', 'WMT', 'COST', 'MCD', 'SBUX',  # Diversified
    'XOM', 'CVX', 'PFE', 'MRK', 'ABBV', 'TMO', 'LLY'  # Energy/Healthcare
]


class Signal:
    """Represents a trading signal."""

    def __init__(self, symbol: str, strategy: str, direction: str,
                 entry_price: float, stop_loss: float, take_profit: float,
                 position_size: int, confidence: float, date: datetime):
        self.symbol = symbol
        self.strategy = strategy
        self.direction = direction
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size
        self.confidence = confidence
        self.date = date

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'strategy': self.strategy,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'risk_reward': (self.take_profit - self.entry_price) /
                          (self.entry_price - self.stop_loss) if self.entry_price != self.stop_loss else 0,
            'confidence': self.confidence,
            'date': self.date.strftime('%Y-%m-%d')
        }

    def __str__(self) -> str:
        rr = (self.take_profit - self.entry_price) / (self.entry_price - self.stop_loss) \
            if self.entry_price != self.stop_loss else 0
        return (f"{self.symbol} | {self.direction.upper()} | {self.strategy}\n"
                f"  Entry: ${self.entry_price:.2f} | Stop: ${self.stop_loss:.2f} | "
                f"Target: ${self.take_profit:.2f}\n"
                f"  Position: {self.position_size} shares | R:R = 1:{rr:.1f} | "
                f"Confidence: {self.confidence:.0%}")


class DailyScanner:
    """
    Scans the market daily for trading signals across multiple strategies.
    """

    def __init__(self, strategies: List[str] = None,
                 watchlist: List[str] = None,
                 capital: float = 100_000):
        """
        Initialize daily scanner.

        Args:
            strategies: List of strategy names to use (default: top performing)
            watchlist: List of symbols to scan
            capital: Trading capital for position sizing
        """
        # Default to balanced mix of strategies if not specified
        self.strategies = strategies or [
            'rsi_oversold', 'bollinger_snapback', 'ema_crossover',
            'macd_bullish', 'supertrend', 'donchian_breakout',
            'volume_breakout', 'inside_bar', 'obv_divergence'
        ]

        self.watchlist = watchlist or DEFAULT_WATCHLIST
        self.capital = capital

        # Risk manager
        self.risk_manager = RiskManager(
            RiskConfig(
                max_risk_per_trade_pct=2.0,
                max_position_size_pct=20.0,
                max_positions=5
            ),
            initial_capital=capital
        )

        # Cache for downloaded data
        self.data_cache: Dict[str, pd.DataFrame] = {}

    def download_data(self, symbol: str, days: int = 100) -> Optional[pd.DataFrame]:
        """
        Download recent data for a symbol.

        Args:
            symbol: Ticker symbol
            days: Number of days of history

        Returns:
            DataFrame with OHLCV data
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=days * 1.5)  # Extra buffer for weekends

            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end)

            if df.empty:
                return None

            # Standardize columns
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            df.index = df.index.tz_localize(None)

            # Keep essential columns
            keep_cols = ['open', 'high', 'low', 'close', 'volume']
            df = df[[c for c in keep_cols if c in df.columns]]

            return df

        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
            return None

    def scan_symbol(self, symbol: str, df: pd.DataFrame = None) -> List[Signal]:
        """
        Scan a single symbol for signals across all strategies.

        Args:
            symbol: Ticker symbol
            df: Price DataFrame (downloads if not provided)

        Returns:
            List of Signal objects
        """
        # Get data
        if df is None:
            df = self.download_data(symbol)
            if df is None or len(df) < 50:
                return []

        signals = []

        # Get current price info
        current_price = df['close'].iloc[-1]
        atr = ti.atr(df, 14).iloc[-1]

        # Run each strategy
        for strategy_name in self.strategies:
            if strategy_name not in STRATEGY_REGISTRY:
                continue

            strategy_func, category, description = STRATEGY_REGISTRY[strategy_name]

            try:
                # Get strategy signals
                strat_signal = strategy_func(df)

                # Check for entry signal on most recent bar
                if strat_signal.entry.iloc[-1]:
                    # Calculate stop loss
                    if strat_signal.stop_loss is not None:
                        stop_loss = strat_signal.stop_loss.iloc[-1]
                    else:
                        stop_loss = current_price - (1.5 * atr)

                    # Ensure stop is reasonable
                    stop_loss = max(stop_loss, current_price * 0.94)

                    # Calculate take profit
                    if strat_signal.take_profit is not None:
                        take_profit = strat_signal.take_profit.iloc[-1]
                    else:
                        risk = current_price - stop_loss
                        take_profit = current_price + (2.5 * risk)

                    # Calculate position size
                    shares, _, _ = self.risk_manager.calculate_position_size(
                        symbol, current_price, stop_loss, self.capital
                    )

                    # Calculate confidence based on signal strength
                    confidence = self._calculate_confidence(df, strategy_name)

                    if shares > 0:
                        signal = Signal(
                            symbol=symbol,
                            strategy=strategy_name,
                            direction='long',
                            entry_price=current_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            position_size=shares,
                            confidence=confidence,
                            date=df.index[-1]
                        )
                        signals.append(signal)

            except Exception as e:
                continue

        return signals

    def _calculate_confidence(self, df: pd.DataFrame, strategy: str) -> float:
        """
        Calculate confidence score for a signal.

        Args:
            df: Price DataFrame
            strategy: Strategy name

        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence

        try:
            # Trend alignment bonus
            ema_20 = ti.ema(df['close'], 20).iloc[-1]
            ema_50 = ti.ema(df['close'], 50).iloc[-1]
            if df['close'].iloc[-1] > ema_20 > ema_50:
                confidence += 0.15

            # Volume confirmation
            volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]
            if volume_ratio > 1.5:
                confidence += 0.1

            # RSI not overbought
            rsi = ti.rsi(df['close'], 14).iloc[-1]
            if 40 < rsi < 70:
                confidence += 0.1

            # Recent momentum
            roc = ti.roc(df['close'], 5).iloc[-1]
            if roc > 0:
                confidence += 0.1

            # Low volatility entry
            bb_bandwidth = ti.bollinger_bandwidth(df['close'], 20).iloc[-1]
            if bb_bandwidth < 10:
                confidence += 0.05

        except Exception:
            pass

        return min(confidence, 1.0)

    def scan_all(self, verbose: bool = True) -> List[Signal]:
        """
        Scan all symbols in watchlist.

        Args:
            verbose: Print progress

        Returns:
            List of all signals found
        """
        all_signals = []

        if verbose:
            print(f"Scanning {len(self.watchlist)} symbols...")
            print(f"Using strategies: {', '.join(self.strategies)}")
            print("-" * 60)

        for i, symbol in enumerate(self.watchlist):
            if verbose and (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(self.watchlist)}")

            signals = self.scan_symbol(symbol)
            all_signals.extend(signals)

        # Sort by confidence
        all_signals.sort(key=lambda s: s.confidence, reverse=True)

        if verbose:
            print(f"\nFound {len(all_signals)} signals")

        return all_signals

    def get_market_context(self) -> Dict:
        """
        Get current market context (SPY trend, VIX level).

        Returns:
            Dictionary with market context
        """
        context = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'spy_trend': 'Unknown',
            'vix_level': 0,
            'market_regime': 'Unknown'
        }

        try:
            # SPY analysis
            spy = self.download_data('SPY', 60)
            if spy is not None:
                ema_20 = ti.ema(spy['close'], 20).iloc[-1]
                ema_50 = ti.ema(spy['close'], 50).iloc[-1]
                current = spy['close'].iloc[-1]

                if current > ema_20 > ema_50:
                    context['spy_trend'] = 'Bullish'
                elif current < ema_20 < ema_50:
                    context['spy_trend'] = 'Bearish'
                else:
                    context['spy_trend'] = 'Neutral'

                context['spy_price'] = current
                context['spy_change_pct'] = ((current / spy['close'].iloc[-2]) - 1) * 100

            # VIX analysis
            vix = self.download_data('^VIX', 30)
            if vix is not None:
                context['vix_level'] = vix['close'].iloc[-1]

                if context['vix_level'] > 30:
                    context['market_regime'] = 'High Volatility'
                elif context['vix_level'] > 25:
                    context['market_regime'] = 'Elevated Volatility'
                elif context['vix_level'] < 15:
                    context['market_regime'] = 'Low Volatility'
                else:
                    context['market_regime'] = 'Normal'

        except Exception as e:
            print(f"Error getting market context: {e}")

        return context

    def generate_signals_file(self, signals: List[Signal],
                              filename: str = 'signals_today.txt') -> str:
        """
        Generate a text file with today's signals.

        Args:
            signals: List of Signal objects
            filename: Output filename

        Returns:
            Filepath of generated file
        """
        context = self.get_market_context()

        lines = []
        lines.append("=" * 70)
        lines.append(f"DAILY TRADING SIGNALS - {context['date']}")
        lines.append("=" * 70)

        lines.append("\nMARKET CONTEXT:")
        lines.append(f"  SPY Trend: {context['spy_trend']}")
        lines.append(f"  VIX Level: {context['vix_level']:.1f}")
        lines.append(f"  Market Regime: {context['market_regime']}")

        lines.append("\n" + "=" * 70)
        lines.append(f"SIGNALS FOUND: {len(signals)}")
        lines.append("=" * 70)

        if not signals:
            lines.append("\nNo signals found for today.")
        else:
            for i, signal in enumerate(signals[:20], 1):  # Top 20
                lines.append(f"\n{i}. {signal}")

        lines.append("\n" + "=" * 70)
        lines.append("RISK MANAGEMENT NOTES:")
        lines.append("=" * 70)
        lines.append("- Never risk more than 2% of capital per trade")
        lines.append("- Maximum 5 concurrent positions")
        lines.append("- Always use stop losses")
        lines.append("- Enter at market open next day")
        lines.append("- Reduce position sizes in high volatility regimes")

        lines.append(f"\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        content = "\n".join(lines)

        with open(filename, 'w') as f:
            f.write(content)

        return filename

    def generate_watchlist(self, signals: List[Signal],
                          days_ahead: int = 5,
                          filename: str = 'watchlist.csv') -> str:
        """
        Generate watchlist CSV for upcoming setups.

        Args:
            signals: List of signals
            days_ahead: Number of days to watch
            filename: Output filename

        Returns:
            Filepath of generated file
        """
        records = []

        for signal in signals[:20]:  # Top 20 setups
            records.append({
                'symbol': signal.symbol,
                'strategy': signal.strategy,
                'direction': signal.direction,
                'entry_price': round(signal.entry_price, 2),
                'stop_loss': round(signal.stop_loss, 2),
                'take_profit': round(signal.take_profit, 2),
                'position_size': signal.position_size,
                'risk_reward': round((signal.take_profit - signal.entry_price) /
                                    (signal.entry_price - signal.stop_loss), 2),
                'confidence': round(signal.confidence, 2),
                'signal_date': signal.date.strftime('%Y-%m-%d'),
                'valid_until': (signal.date + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            })

        df = pd.DataFrame(records)
        df.to_csv(filename, index=False)

        return filename

    def run_daily_scan(self, output_dir: str = '.') -> Tuple[List[Signal], str, str]:
        """
        Run complete daily scan and generate all outputs.

        Args:
            output_dir: Directory for output files

        Returns:
            Tuple of (signals, signals_filepath, watchlist_filepath)
        """
        print("\n" + "=" * 70)
        print("DAILY MARKET SCANNER")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)

        # Get market context
        context = self.get_market_context()
        print(f"\nMarket Context:")
        print(f"  SPY: {context.get('spy_trend', 'Unknown')} "
              f"(${context.get('spy_price', 0):.2f})")
        print(f"  VIX: {context.get('vix_level', 0):.1f}")
        print(f"  Regime: {context.get('market_regime', 'Unknown')}")

        # Scan all symbols
        print(f"\nScanning {len(self.watchlist)} symbols...")
        signals = self.scan_all(verbose=True)

        # Generate output files
        signals_file = os.path.join(output_dir, 'signals_today.txt')
        self.generate_signals_file(signals, signals_file)
        print(f"\nSignals saved to: {signals_file}")

        watchlist_file = os.path.join(output_dir, 'watchlist.csv')
        self.generate_watchlist(signals, filename=watchlist_file)
        print(f"Watchlist saved to: {watchlist_file}")

        # Print top signals
        print("\n" + "=" * 70)
        print("TOP 5 SIGNALS")
        print("=" * 70)

        for signal in signals[:5]:
            print(f"\n{signal}")

        return signals, signals_file, watchlist_file


def scan_single_symbol(symbol: str, strategies: List[str] = None) -> List[Signal]:
    """
    Quick scan for a single symbol.

    Args:
        symbol: Ticker symbol
        strategies: Strategies to use

    Returns:
        List of signals
    """
    scanner = DailyScanner(strategies=strategies)
    return scanner.scan_symbol(symbol)


def main():
    """Main entry point for daily scanner."""
    import argparse

    parser = argparse.ArgumentParser(description='Daily Market Scanner')
    parser.add_argument('--symbols', nargs='+', help='Symbols to scan')
    parser.add_argument('--strategies', nargs='+', help='Strategies to use')
    parser.add_argument('--capital', type=float, default=100000, help='Trading capital')
    parser.add_argument('--output', default='.', help='Output directory')

    args = parser.parse_args()

    # Initialize scanner
    scanner = DailyScanner(
        strategies=args.strategies,
        watchlist=args.symbols,
        capital=args.capital
    )

    # Run scan
    signals, signals_file, watchlist_file = scanner.run_daily_scan(output_dir=args.output)

    print("\n" + "=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)
    print(f"Total signals found: {len(signals)}")
    print(f"Signals file: {signals_file}")
    print(f"Watchlist file: {watchlist_file}")


if __name__ == '__main__':
    main()

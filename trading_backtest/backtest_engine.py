"""
Backtest Engine Module for Stock Trading Backtest System
Runs strategies, tracks trades, and calculates performance metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import warnings

from strategies import StrategySignal, get_all_strategies, get_strategy
from indicators import TechnicalIndicators as ti

warnings.filterwarnings('ignore')


@dataclass
class Trade:
    """Represents a single trade."""
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    shares: int = 0
    direction: str = 'long'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_reason: str = ''
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    initial_capital: float = 100_000
    commission_per_trade: float = 1.0
    slippage_pct: float = 0.0005  # 0.05%
    max_positions: int = 5
    position_size_pct: float = 0.02  # 2% risk per trade
    max_risk_pct: float = 0.06  # 6% max stop loss
    default_atr_mult: float = 1.5  # Default stop loss multiplier
    min_reward_risk: float = 2.0  # Minimum reward:risk ratio
    use_next_day_open: bool = True  # Enter at next day's open
    allow_partial_fills: bool = False


@dataclass
class BacktestResults:
    """Container for backtest results."""
    strategy_name: str
    trades: List[Trade]
    equity_curve: pd.Series
    daily_returns: pd.Series
    metrics: Dict[str, float]
    trade_log: pd.DataFrame
    config: BacktestConfig


class BacktestEngine:
    """
    Main backtesting engine for running trading strategies.
    """

    def __init__(self, config: BacktestConfig = None):
        """
        Initialize backtest engine.

        Args:
            config: BacktestConfig object with parameters
        """
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Trade] = {}
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.capital = self.config.initial_capital

    def reset(self):
        """Reset engine state for new backtest."""
        self.trades = []
        self.open_positions = {}
        self.equity_curve = []
        self.capital = self.config.initial_capital

    def calculate_position_size(self, price: float, stop_loss: float,
                                atr: float = None) -> Tuple[int, float]:
        """
        Calculate position size based on risk management rules.

        Args:
            price: Entry price
            stop_loss: Stop loss price
            atr: Average True Range (optional)

        Returns:
            Tuple of (shares, actual_risk_pct)
        """
        # Calculate risk per share
        risk_per_share = abs(price - stop_loss)

        if risk_per_share == 0:
            risk_per_share = price * 0.02  # Default 2% risk if no stop

        # Max risk amount per trade
        max_risk_amount = self.capital * self.config.position_size_pct

        # Calculate shares
        shares = int(max_risk_amount / risk_per_share)

        # Check position size limits
        max_position_value = self.capital * 0.2  # Max 20% of capital per position
        max_shares_by_value = int(max_position_value / price)
        shares = min(shares, max_shares_by_value)

        # Ensure at least 1 share
        shares = max(1, shares)

        # Calculate actual risk
        actual_risk_pct = (shares * risk_per_share) / self.capital

        return shares, actual_risk_pct

    def apply_slippage(self, price: float, direction: str, is_entry: bool) -> float:
        """
        Apply slippage to a price.

        Args:
            price: Original price
            direction: 'long' or 'short'
            is_entry: True for entry, False for exit

        Returns:
            Adjusted price
        """
        slippage = price * self.config.slippage_pct

        if direction == 'long':
            if is_entry:
                return price + slippage  # Pay more to enter
            else:
                return price - slippage  # Get less to exit
        else:
            if is_entry:
                return price - slippage  # Get less to enter short
            else:
                return price + slippage  # Pay more to cover

    def run_backtest(self, df: pd.DataFrame, signal: StrategySignal,
                     symbol: str = 'UNKNOWN') -> List[Trade]:
        """
        Run backtest for a single symbol with given signals.

        Args:
            df: Price DataFrame with OHLCV
            signal: StrategySignal with entry/exit signals
            symbol: Ticker symbol

        Returns:
            List of completed trades
        """
        trades = []
        position: Optional[Trade] = None

        # Calculate ATR for default stop loss
        atr = ti.atr(df, 14)

        for i in range(1, len(df)):
            date = df.index[i]
            prev_date = df.index[i-1]

            # Current prices
            open_price = df['open'].iloc[i]
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]
            close = df['close'].iloc[i]

            # Check if we have an open position
            if position is not None:
                # Check stop loss
                if position.stop_loss and low <= position.stop_loss:
                    exit_price = self.apply_slippage(position.stop_loss, 'long', False)
                    position.exit_date = date
                    position.exit_price = exit_price
                    position.exit_reason = 'Stop Loss'
                    position.pnl = (exit_price - position.entry_price) * position.shares - position.commission
                    position.pnl_pct = (exit_price / position.entry_price - 1) * 100
                    trades.append(position)
                    position = None
                    continue

                # Check take profit
                if position.take_profit and high >= position.take_profit:
                    exit_price = self.apply_slippage(position.take_profit, 'long', False)
                    position.exit_date = date
                    position.exit_price = exit_price
                    position.exit_reason = 'Take Profit'
                    position.pnl = (exit_price - position.entry_price) * position.shares - position.commission
                    position.pnl_pct = (exit_price / position.entry_price - 1) * 100
                    trades.append(position)
                    position = None
                    continue

                # Check exit signal (from previous day's close)
                if signal.exit.iloc[i-1]:
                    exit_price = self.apply_slippage(open_price, 'long', False)
                    position.exit_date = date
                    position.exit_price = exit_price
                    position.exit_reason = 'Exit Signal'
                    position.pnl = (exit_price - position.entry_price) * position.shares - position.commission
                    position.pnl_pct = (exit_price / position.entry_price - 1) * 100
                    trades.append(position)
                    position = None
                    continue

            # Check entry signal (from previous day's close)
            if position is None and signal.entry.iloc[i-1]:
                entry_price = self.apply_slippage(open_price, 'long', True)

                # Calculate stop loss
                if signal.stop_loss is not None and not pd.isna(signal.stop_loss.iloc[i-1]):
                    stop_loss = signal.stop_loss.iloc[i-1]
                else:
                    stop_loss = entry_price - (self.config.default_atr_mult * atr.iloc[i-1])

                # Ensure stop is not too far (max risk)
                max_stop = entry_price * (1 - self.config.max_risk_pct)
                stop_loss = max(stop_loss, max_stop)

                # Calculate take profit
                if signal.take_profit is not None and not pd.isna(signal.take_profit.iloc[i-1]):
                    take_profit = signal.take_profit.iloc[i-1]
                else:
                    risk = entry_price - stop_loss
                    take_profit = entry_price + (self.config.min_reward_risk * risk)

                # Calculate position size
                shares, actual_risk = self.calculate_position_size(entry_price, stop_loss, atr.iloc[i-1])

                # Create trade
                position = Trade(
                    symbol=symbol,
                    entry_date=date,
                    entry_price=entry_price,
                    shares=shares,
                    direction='long',
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    commission=self.config.commission_per_trade * 2  # Entry + exit
                )

        # Close any remaining position at the end
        if position is not None:
            exit_price = self.apply_slippage(df['close'].iloc[-1], 'long', False)
            position.exit_date = df.index[-1]
            position.exit_price = exit_price
            position.exit_reason = 'End of Backtest'
            position.pnl = (exit_price - position.entry_price) * position.shares - position.commission
            position.pnl_pct = (exit_price / position.entry_price - 1) * 100
            trades.append(position)

        return trades

    def run_portfolio_backtest(self, stock_data: Dict[str, pd.DataFrame],
                               strategy_func: Callable,
                               strategy_name: str,
                               params: dict = None,
                               start_date: str = None,
                               end_date: str = None) -> BacktestResults:
        """
        Run backtest across multiple stocks with portfolio constraints.

        Args:
            stock_data: Dictionary of DataFrames by symbol
            strategy_func: Strategy function to test
            strategy_name: Name of the strategy
            params: Strategy parameters
            start_date: Start date for backtest
            end_date: End date for backtest

        Returns:
            BacktestResults object
        """
        self.reset()
        all_trades = []

        # Collect all signals
        signals_by_symbol = {}
        for symbol, df in stock_data.items():
            try:
                if start_date:
                    df = df[df.index >= pd.Timestamp(start_date)]
                if end_date:
                    df = df[df.index <= pd.Timestamp(end_date)]

                if len(df) < 50:  # Skip if insufficient data
                    continue

                signal = strategy_func(df, params)
                signals_by_symbol[symbol] = (df, signal)
            except Exception as e:
                continue

        # Run backtests for each symbol
        for symbol, (df, signal) in signals_by_symbol.items():
            trades = self.run_backtest(df, signal, symbol)
            all_trades.extend(trades)

        # Sort trades by entry date
        all_trades.sort(key=lambda t: t.entry_date)

        # Build equity curve
        equity_curve = self._build_equity_curve(all_trades, stock_data, start_date, end_date)

        # Calculate metrics
        metrics = self.calculate_metrics(all_trades, equity_curve)

        # Build trade log
        trade_log = self._build_trade_log(all_trades)

        return BacktestResults(
            strategy_name=strategy_name,
            trades=all_trades,
            equity_curve=equity_curve,
            daily_returns=equity_curve.pct_change().dropna(),
            metrics=metrics,
            trade_log=trade_log,
            config=self.config
        )

    def _build_equity_curve(self, trades: List[Trade],
                            stock_data: Dict[str, pd.DataFrame],
                            start_date: str = None,
                            end_date: str = None) -> pd.Series:
        """Build equity curve from trades."""
        if not trades:
            # Return flat equity curve
            if 'SPY' in stock_data:
                dates = stock_data['SPY'].index
                if start_date:
                    dates = dates[dates >= pd.Timestamp(start_date)]
                if end_date:
                    dates = dates[dates <= pd.Timestamp(end_date)]
                return pd.Series(self.config.initial_capital, index=dates)
            return pd.Series([self.config.initial_capital])

        # Get date range from trades
        all_dates = set()
        for symbol, df in stock_data.items():
            all_dates.update(df.index.tolist())

        all_dates = sorted(all_dates)
        if start_date:
            all_dates = [d for d in all_dates if d >= pd.Timestamp(start_date)]
        if end_date:
            all_dates = [d for d in all_dates if d <= pd.Timestamp(end_date)]

        # Initialize equity
        equity = pd.Series(index=all_dates, dtype=float)
        equity.iloc[0] = self.config.initial_capital

        # Track running P&L
        cumulative_pnl = 0

        # Create trade lookup by exit date
        trades_by_exit = {}
        for trade in trades:
            if trade.exit_date:
                if trade.exit_date not in trades_by_exit:
                    trades_by_exit[trade.exit_date] = []
                trades_by_exit[trade.exit_date].append(trade)

        # Build curve
        for i, date in enumerate(all_dates):
            if date in trades_by_exit:
                for trade in trades_by_exit[date]:
                    cumulative_pnl += trade.pnl

            equity.iloc[i] = self.config.initial_capital + cumulative_pnl

        # Forward fill any NaN values
        equity = equity.ffill()

        return equity

    def _build_trade_log(self, trades: List[Trade]) -> pd.DataFrame:
        """Build DataFrame trade log."""
        if not trades:
            return pd.DataFrame()

        records = []
        for t in trades:
            records.append({
                'symbol': t.symbol,
                'entry_date': t.entry_date,
                'entry_price': t.entry_price,
                'exit_date': t.exit_date,
                'exit_price': t.exit_price,
                'shares': t.shares,
                'direction': t.direction,
                'stop_loss': t.stop_loss,
                'take_profit': t.take_profit,
                'exit_reason': t.exit_reason,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'commission': t.commission
            })

        return pd.DataFrame(records)

    def calculate_metrics(self, trades: List[Trade], equity_curve: pd.Series) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.

        Args:
            trades: List of completed trades
            equity_curve: Series of portfolio values

        Returns:
            Dictionary of metrics
        """
        metrics = {}

        # Basic trade statistics
        metrics['total_trades'] = len(trades)

        if not trades:
            return self._empty_metrics()

        # Win/Loss analysis
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]

        metrics['winning_trades'] = len(wins)
        metrics['losing_trades'] = len(losses)
        metrics['win_rate'] = len(wins) / len(trades) * 100 if trades else 0

        # P&L metrics
        total_pnl = sum(t.pnl for t in trades)
        metrics['total_pnl'] = total_pnl
        metrics['total_return_pct'] = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100

        # Average trade
        metrics['avg_pnl'] = np.mean([t.pnl for t in trades])
        metrics['avg_pnl_pct'] = np.mean([t.pnl_pct for t in trades])
        metrics['avg_win'] = np.mean([t.pnl for t in wins]) if wins else 0
        metrics['avg_loss'] = np.mean([t.pnl for t in losses]) if losses else 0
        metrics['avg_win_pct'] = np.mean([t.pnl_pct for t in wins]) if wins else 0
        metrics['avg_loss_pct'] = np.mean([t.pnl_pct for t in losses]) if losses else 0

        # Profit factor
        gross_profit = sum(t.pnl for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl for t in losses)) if losses else 1
        metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else 0

        # Risk-adjusted returns
        daily_returns = equity_curve.pct_change().dropna()

        # Sharpe Ratio (annualized, assuming 252 trading days)
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            metrics['sharpe_ratio'] = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            metrics['sharpe_ratio'] = 0

        # Sortino Ratio (downside deviation only)
        downside_returns = daily_returns[daily_returns < 0]
        if len(downside_returns) > 1 and downside_returns.std() > 0:
            metrics['sortino_ratio'] = (daily_returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            metrics['sortino_ratio'] = metrics['sharpe_ratio']

        # Maximum Drawdown
        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve - rolling_max) / rolling_max
        metrics['max_drawdown_pct'] = abs(drawdown.min()) * 100

        # Calmar Ratio (annual return / max drawdown)
        years = len(equity_curve) / 252
        if years > 0 and metrics['max_drawdown_pct'] > 0:
            annual_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1/years) - 1
            metrics['calmar_ratio'] = (annual_return * 100) / metrics['max_drawdown_pct']
            metrics['annual_return_pct'] = annual_return * 100
        else:
            metrics['calmar_ratio'] = 0
            metrics['annual_return_pct'] = metrics['total_return_pct'] / max(years, 1)

        # Recovery Factor
        if metrics['max_drawdown_pct'] > 0:
            metrics['recovery_factor'] = metrics['total_return_pct'] / metrics['max_drawdown_pct']
        else:
            metrics['recovery_factor'] = 0

        # Trade duration
        durations = []
        for t in trades:
            if t.exit_date and t.entry_date:
                durations.append((t.exit_date - t.entry_date).days)
        metrics['avg_trade_duration_days'] = np.mean(durations) if durations else 0

        # Consecutive wins/losses
        pnl_signs = [1 if t.pnl > 0 else -1 for t in trades]
        metrics['max_consecutive_wins'] = self._max_consecutive(pnl_signs, 1)
        metrics['max_consecutive_losses'] = self._max_consecutive(pnl_signs, -1)

        # Expectancy
        if trades:
            win_rate = metrics['win_rate'] / 100
            metrics['expectancy'] = (win_rate * metrics['avg_win']) - ((1 - win_rate) * abs(metrics['avg_loss']))
        else:
            metrics['expectancy'] = 0

        # Yearly breakdown
        yearly_returns = self._calculate_yearly_returns(equity_curve)
        metrics['positive_years'] = sum(1 for r in yearly_returns.values() if r > 0)
        metrics['total_years'] = len(yearly_returns)
        metrics['yearly_returns'] = yearly_returns

        return metrics

    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dictionary."""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'total_return_pct': 0,
            'avg_pnl': 0,
            'avg_pnl_pct': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_win_pct': 0,
            'avg_loss_pct': 0,
            'profit_factor': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown_pct': 0,
            'calmar_ratio': 0,
            'annual_return_pct': 0,
            'recovery_factor': 0,
            'avg_trade_duration_days': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'expectancy': 0,
            'positive_years': 0,
            'total_years': 0,
            'yearly_returns': {}
        }

    def _max_consecutive(self, values: List[int], target: int) -> int:
        """Find maximum consecutive occurrences of target value."""
        max_count = 0
        current_count = 0
        for v in values:
            if v == target:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        return max_count

    def _calculate_yearly_returns(self, equity_curve: pd.Series) -> Dict[int, float]:
        """Calculate returns by year."""
        yearly = {}
        years = equity_curve.index.year.unique()

        for year in years:
            year_data = equity_curve[equity_curve.index.year == year]
            if len(year_data) > 1:
                ret = (year_data.iloc[-1] / year_data.iloc[0] - 1) * 100
                yearly[year] = ret

        return yearly


def validate_strategy(results: BacktestResults,
                      min_win_rate: float = 42,
                      min_profit_factor: float = 1.5,
                      min_sharpe: float = 0.7,
                      max_drawdown: float = 30,
                      min_trades: int = 200,
                      min_positive_years: int = 6) -> Tuple[bool, List[str]]:
    """
    Validate if strategy passes all criteria.

    Args:
        results: BacktestResults object
        min_win_rate: Minimum win rate %
        min_profit_factor: Minimum profit factor
        min_sharpe: Minimum Sharpe ratio
        max_drawdown: Maximum drawdown %
        min_trades: Minimum number of trades
        min_positive_years: Minimum positive years out of 10

    Returns:
        Tuple of (passed, list of failures)
    """
    failures = []
    metrics = results.metrics

    if metrics['total_trades'] < min_trades:
        failures.append(f"Insufficient trades: {metrics['total_trades']} < {min_trades}")

    if metrics['win_rate'] < min_win_rate:
        failures.append(f"Low win rate: {metrics['win_rate']:.1f}% < {min_win_rate}%")

    if metrics['profit_factor'] < min_profit_factor:
        failures.append(f"Low profit factor: {metrics['profit_factor']:.2f} < {min_profit_factor}")

    if metrics['sharpe_ratio'] < min_sharpe:
        failures.append(f"Low Sharpe ratio: {metrics['sharpe_ratio']:.2f} < {min_sharpe}")

    if metrics['max_drawdown_pct'] > max_drawdown:
        failures.append(f"High drawdown: {metrics['max_drawdown_pct']:.1f}% > {max_drawdown}%")

    if metrics['positive_years'] < min_positive_years:
        failures.append(f"Few positive years: {metrics['positive_years']} < {min_positive_years}")

    return len(failures) == 0, failures


def compare_to_benchmark(results: BacktestResults,
                         benchmark_returns: pd.Series,
                         min_alpha: float = 3.0) -> Tuple[bool, float]:
    """
    Compare strategy to buy-and-hold benchmark.

    Args:
        results: BacktestResults object
        benchmark_returns: Benchmark returns series
        min_alpha: Minimum annual alpha required

    Returns:
        Tuple of (beats_benchmark, alpha)
    """
    # Align dates
    strategy_returns = results.daily_returns
    common_dates = strategy_returns.index.intersection(benchmark_returns.index)

    if len(common_dates) < 252:  # Less than a year of data
        return False, 0

    strat = strategy_returns.loc[common_dates]
    bench = benchmark_returns.loc[common_dates]

    # Calculate annual returns
    years = len(common_dates) / 252
    strat_annual = ((1 + strat).prod() ** (1/years) - 1) * 100
    bench_annual = ((1 + bench).prod() ** (1/years) - 1) * 100

    alpha = strat_annual - bench_annual

    return alpha >= min_alpha, alpha


if __name__ == '__main__':
    # Test backtest engine
    import yfinance as yf
    from strategies import TradingStrategies

    print("Testing Backtest Engine...")
    print("-" * 50)

    # Download sample data
    ticker = yf.Ticker('SPY')
    df = ticker.history(start='2015-01-01', end='2024-01-01')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    df.index = df.index.tz_localize(None)

    print(f"Loaded {len(df)} days of SPY data\n")

    # Create engine
    config = BacktestConfig(
        initial_capital=100_000,
        commission_per_trade=1.0,
        slippage_pct=0.0005,
        position_size_pct=0.02
    )
    engine = BacktestEngine(config)

    # Test a strategy
    print("Testing RSI Oversold strategy...")
    signal = TradingStrategies.strategy_01_rsi_oversold(df)
    trades = engine.run_backtest(df, signal, 'SPY')

    print(f"\nTotal trades: {len(trades)}")

    if trades:
        print(f"\nSample trades:")
        for t in trades[:5]:
            print(f"  {t.entry_date.date()} -> {t.exit_date.date() if t.exit_date else 'Open'}: "
                  f"${t.entry_price:.2f} -> ${t.exit_price:.2f if t.exit_price else 0:.2f}, "
                  f"P&L: ${t.pnl:.2f} ({t.pnl_pct:.1f}%), Reason: {t.exit_reason}")

        # Calculate metrics
        equity = engine._build_equity_curve(trades, {'SPY': df})
        metrics = engine.calculate_metrics(trades, equity)

        print(f"\n" + "=" * 50)
        print("PERFORMANCE METRICS")
        print("=" * 50)
        print(f"Win Rate:       {metrics['win_rate']:.1f}%")
        print(f"Profit Factor:  {metrics['profit_factor']:.2f}")
        print(f"Sharpe Ratio:   {metrics['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio:  {metrics['sortino_ratio']:.2f}")
        print(f"Max Drawdown:   {metrics['max_drawdown_pct']:.1f}%")
        print(f"Total Return:   {metrics['total_return_pct']:.1f}%")
        print(f"Annual Return:  {metrics['annual_return_pct']:.1f}%")
        print(f"Calmar Ratio:   {metrics['calmar_ratio']:.2f}")

        # Validate
        passed, failures = validate_strategy(
            BacktestResults(
                strategy_name='test',
                trades=trades,
                equity_curve=equity,
                daily_returns=equity.pct_change().dropna(),
                metrics=metrics,
                trade_log=engine._build_trade_log(trades),
                config=config
            ),
            min_trades=10  # Lower for testing
        )

        print(f"\nValidation: {'PASSED' if passed else 'FAILED'}")
        if failures:
            for f in failures:
                print(f"  - {f}")

    print("\nBacktest engine test completed!")

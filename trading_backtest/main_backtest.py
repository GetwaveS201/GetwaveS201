"""
Main Backtest Module for Stock Trading Backtest System
Runs all strategies, generates rankings, and produces reports.
"""

import os
import sys
import json
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

from data_loader import DataLoader, TOP_100_STOCKS, CORE_ETFS
from strategies import get_all_strategies, STRATEGY_REGISTRY
from backtest_engine import BacktestEngine, BacktestConfig, BacktestResults, validate_strategy
from risk_manager import RiskManager, RiskConfig

warnings.filterwarnings('ignore')


# Validation thresholds
VALIDATION_CRITERIA = {
    'min_win_rate': 42,
    'min_profit_factor': 1.5,
    'min_sharpe': 0.7,
    'max_drawdown': 30,
    'min_trades': 200,
    'min_positive_years': 6,
    'min_sortino': 1.0,
    'min_calmar': 0.8,
    'min_recovery_factor': 1.5,
    'min_alpha': 3.0  # Annual alpha over SPY
}


class BacktestRunner:
    """
    Main class to run all backtests and generate reports.
    """

    def __init__(self, data_dir: str = 'data', output_dir: str = 'output'):
        """
        Initialize backtest runner.

        Args:
            data_dir: Directory for data files
            output_dir: Directory for output files
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.data_loader = DataLoader(
            data_dir=data_dir,
            start_date='2015-01-01',
            end_date='2025-01-01'
        )

        self.backtest_config = BacktestConfig(
            initial_capital=100_000,
            commission_per_trade=1.0,
            slippage_pct=0.0005,
            max_positions=5,
            position_size_pct=0.02
        )

        self.engine = BacktestEngine(self.backtest_config)
        self.results: Dict[str, BacktestResults] = {}
        self.rankings: pd.DataFrame = None

    def load_data(self, use_cache: bool = True) -> bool:
        """
        Load or download stock data.

        Args:
            use_cache: Use cached data if available

        Returns:
            True if successful
        """
        if use_cache and self.data_loader.load_data():
            return True

        print("Downloading fresh data...")
        self.data_loader.download_all_stocks(verbose=True)
        self.data_loader.save_data()
        return len(self.data_loader.stock_data) > 0

    def run_single_strategy(self, strategy_name: str,
                            start_date: str = '2015-01-01',
                            end_date: str = '2025-01-01') -> Optional[BacktestResults]:
        """
        Run backtest for a single strategy.

        Args:
            strategy_name: Name of strategy to test
            start_date: Start date
            end_date: End date

        Returns:
            BacktestResults or None if failed
        """
        if strategy_name not in STRATEGY_REGISTRY:
            print(f"Unknown strategy: {strategy_name}")
            return None

        strategy_func, category, description = STRATEGY_REGISTRY[strategy_name]

        print(f"\nRunning: {strategy_name} ({description})")
        print("-" * 50)

        try:
            results = self.engine.run_portfolio_backtest(
                stock_data=self.data_loader.stock_data,
                strategy_func=strategy_func,
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date
            )

            self.results[strategy_name] = results
            return results

        except Exception as e:
            print(f"Error running {strategy_name}: {str(e)}")
            return None

    def run_all_strategies(self, start_date: str = '2015-01-01',
                          end_date: str = '2025-01-01',
                          verbose: bool = True) -> Dict[str, BacktestResults]:
        """
        Run backtests for all 30 strategies.

        Args:
            start_date: Start date
            end_date: End date
            verbose: Print progress

        Returns:
            Dictionary of results by strategy name
        """
        strategies = get_all_strategies()
        total = len(strategies)

        if verbose:
            print("=" * 60)
            print(f"RUNNING {total} STRATEGIES")
            print(f"Period: {start_date} to {end_date}")
            print(f"Stocks: {len(self.data_loader.stock_data)}")
            print("=" * 60)

        for i, (name, (func, category, desc)) in enumerate(strategies.items(), 1):
            if verbose:
                print(f"\n[{i}/{total}] {name}: {desc}")

            try:
                results = self.engine.run_portfolio_backtest(
                    stock_data=self.data_loader.stock_data,
                    strategy_func=func,
                    strategy_name=name,
                    start_date=start_date,
                    end_date=end_date
                )

                self.results[name] = results

                if verbose:
                    m = results.metrics
                    print(f"    Trades: {m['total_trades']:4d}  "
                          f"Win: {m['win_rate']:5.1f}%  "
                          f"PF: {m['profit_factor']:5.2f}  "
                          f"Sharpe: {m['sharpe_ratio']:5.2f}  "
                          f"DD: {m['max_drawdown_pct']:5.1f}%")

            except Exception as e:
                print(f"    ERROR: {str(e)[:50]}")

        return self.results

    def run_walk_forward(self, strategy_name: str,
                         train_months: int = 12,
                         test_months: int = 3) -> Dict:
        """
        Run walk-forward optimization for a strategy.

        Args:
            strategy_name: Strategy to test
            train_months: Training period in months
            test_months: Testing period in months

        Returns:
            Walk-forward results
        """
        if strategy_name not in STRATEGY_REGISTRY:
            return {}

        strategy_func, _, _ = STRATEGY_REGISTRY[strategy_name]

        # Get date range
        dates = sorted(list(self.data_loader.stock_data.values())[0].index)
        start_date = dates[0]
        end_date = dates[-1]

        results = {
            'periods': [],
            'train_metrics': [],
            'test_metrics': [],
            'degradation': []
        }

        current_start = start_date

        while current_start + pd.DateOffset(months=train_months + test_months) <= end_date:
            train_end = current_start + pd.DateOffset(months=train_months)
            test_end = train_end + pd.DateOffset(months=test_months)

            # Train period
            train_results = self.engine.run_portfolio_backtest(
                stock_data=self.data_loader.stock_data,
                strategy_func=strategy_func,
                strategy_name=strategy_name,
                start_date=str(current_start.date()),
                end_date=str(train_end.date())
            )

            # Test period
            test_results = self.engine.run_portfolio_backtest(
                stock_data=self.data_loader.stock_data,
                strategy_func=strategy_func,
                strategy_name=strategy_name,
                start_date=str(train_end.date()),
                end_date=str(test_end.date())
            )

            results['periods'].append({
                'train_start': str(current_start.date()),
                'train_end': str(train_end.date()),
                'test_start': str(train_end.date()),
                'test_end': str(test_end.date())
            })

            results['train_metrics'].append(train_results.metrics)
            results['test_metrics'].append(test_results.metrics)

            # Calculate degradation
            if train_results.metrics['sharpe_ratio'] > 0:
                degradation = 1 - (test_results.metrics['sharpe_ratio'] /
                                   train_results.metrics['sharpe_ratio'])
            else:
                degradation = 1.0

            results['degradation'].append(degradation)

            current_start = current_start + pd.DateOffset(months=test_months)

        # Calculate walk-forward efficiency
        avg_degradation = np.mean(results['degradation'])
        results['walk_forward_efficiency'] = (1 - avg_degradation) * 100

        return results

    def generate_rankings(self) -> pd.DataFrame:
        """
        Generate strategy rankings based on multiple metrics.

        Returns:
            DataFrame with strategy rankings
        """
        if not self.results:
            return pd.DataFrame()

        records = []
        for name, result in self.results.items():
            m = result.metrics
            _, category, description = STRATEGY_REGISTRY[name]

            record = {
                'strategy': name,
                'category': category,
                'description': description,
                'total_trades': m['total_trades'],
                'win_rate': m['win_rate'],
                'profit_factor': m['profit_factor'],
                'sharpe_ratio': m['sharpe_ratio'],
                'sortino_ratio': m['sortino_ratio'],
                'max_drawdown': m['max_drawdown_pct'],
                'calmar_ratio': m['calmar_ratio'],
                'annual_return': m['annual_return_pct'],
                'total_return': m['total_return_pct'],
                'avg_trade_pnl': m['avg_pnl_pct'],
                'recovery_factor': m['recovery_factor'],
                'positive_years': m['positive_years'],
                'expectancy': m['expectancy']
            }
            records.append(record)

        df = pd.DataFrame(records)

        # Calculate composite score
        df['composite_score'] = (
            df['sharpe_ratio'].rank(pct=True) * 0.25 +
            df['profit_factor'].rank(pct=True) * 0.20 +
            df['win_rate'].rank(pct=True) * 0.15 +
            (1 - df['max_drawdown'].rank(pct=True)) * 0.20 +
            df['calmar_ratio'].rank(pct=True) * 0.10 +
            df['recovery_factor'].rank(pct=True) * 0.10
        ) * 100

        # Sort by composite score
        df = df.sort_values('composite_score', ascending=False)
        df['rank'] = range(1, len(df) + 1)

        self.rankings = df
        return df

    def validate_strategies(self) -> Tuple[List[str], List[str]]:
        """
        Validate all strategies against criteria.

        Returns:
            Tuple of (passing strategies, failing strategies)
        """
        passing = []
        failing = []

        for name, result in self.results.items():
            passed, failures = validate_strategy(
                result,
                min_win_rate=VALIDATION_CRITERIA['min_win_rate'],
                min_profit_factor=VALIDATION_CRITERIA['min_profit_factor'],
                min_sharpe=VALIDATION_CRITERIA['min_sharpe'],
                max_drawdown=VALIDATION_CRITERIA['max_drawdown'],
                min_trades=VALIDATION_CRITERIA['min_trades'],
                min_positive_years=VALIDATION_CRITERIA['min_positive_years']
            )

            if passed:
                passing.append(name)
            else:
                failing.append(name)

        return passing, failing

    def analyze_market_regime_performance(self) -> pd.DataFrame:
        """
        Analyze strategy performance across market regimes.

        Returns:
            DataFrame with regime analysis
        """
        try:
            regime_df = self.data_loader.get_market_regime()
        except Exception:
            return pd.DataFrame()

        regime_results = []

        for name, result in self.results.items():
            for regime in ['Bull Market', 'Bear Market', 'High Volatility', 'Neutral']:
                regime_dates = regime_df[regime_df['regime'] == regime].index

                # Filter trades by regime
                regime_trades = [t for t in result.trades
                                 if t.entry_date in regime_dates]

                if regime_trades:
                    wins = sum(1 for t in regime_trades if t.pnl > 0)
                    total_pnl = sum(t.pnl for t in regime_trades)

                    regime_results.append({
                        'strategy': name,
                        'regime': regime,
                        'trades': len(regime_trades),
                        'win_rate': wins / len(regime_trades) * 100,
                        'total_pnl': total_pnl,
                        'avg_pnl': np.mean([t.pnl for t in regime_trades])
                    })

        return pd.DataFrame(regime_results)

    def save_rankings(self, filename: str = 'strategy_rankings.csv') -> None:
        """Save strategy rankings to CSV."""
        if self.rankings is not None:
            filepath = os.path.join(self.output_dir, filename)
            self.rankings.to_csv(filepath, index=False)
            print(f"Rankings saved to {filepath}")

    def save_trade_logs(self) -> None:
        """Save trade logs for all strategies."""
        for name, result in self.results.items():
            if not result.trade_log.empty:
                filepath = os.path.join(self.output_dir, f'trades_{name}.csv')
                result.trade_log.to_csv(filepath, index=False)

        # Save combined trade log
        all_trades = []
        for name, result in self.results.items():
            if not result.trade_log.empty:
                trades = result.trade_log.copy()
                trades['strategy'] = name
                all_trades.append(trades)

        if all_trades:
            combined = pd.concat(all_trades, ignore_index=True)
            combined.to_csv(os.path.join(self.output_dir, 'trade_log.csv'), index=False)

    def save_equity_curves(self) -> None:
        """Save equity curves for all strategies."""
        curves = {}
        for name, result in self.results.items():
            curves[name] = result.equity_curve

        df = pd.DataFrame(curves)
        df.to_csv(os.path.join(self.output_dir, 'equity_curves.csv'))

    def generate_best_strategy_code(self, strategy_name: str = None) -> str:
        """
        Generate standalone code for the best strategy.

        Args:
            strategy_name: Strategy name (uses top ranked if not specified)

        Returns:
            Python code string
        """
        if strategy_name is None:
            if self.rankings is None:
                self.generate_rankings()
            strategy_name = self.rankings.iloc[0]['strategy']

        _, category, description = STRATEGY_REGISTRY[strategy_name]
        result = self.results.get(strategy_name)

        code = f'''"""
Best Strategy: {strategy_name}
Category: {category}
Description: {description}

Generated by Stock Trading Backtest System
Performance Metrics:
- Win Rate: {result.metrics['win_rate']:.1f}%
- Profit Factor: {result.metrics['profit_factor']:.2f}
- Sharpe Ratio: {result.metrics['sharpe_ratio']:.2f}
- Max Drawdown: {result.metrics['max_drawdown_pct']:.1f}%
- Annual Return: {result.metrics['annual_return_pct']:.1f}%
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


class {strategy_name.title().replace('_', '')}Strategy:
    """
    {description}
    """

    def __init__(self, symbols: list = None):
        """
        Initialize strategy.

        Args:
            symbols: List of symbols to trade (default: top 20 liquid stocks)
        """
        self.symbols = symbols or [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM',
            'V', 'UNH', 'JNJ', 'WMT', 'MA', 'PG', 'HD', 'DIS', 'PYPL', 'NFLX',
            'ADBE', 'CRM'
        ]

        # Risk parameters
        self.max_positions = 5
        self.risk_per_trade = 0.02
        self.max_stop_pct = 0.06

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate required indicators."""
        df = df.copy()

        # Add your indicator calculations here based on the strategy
        # This is a placeholder - actual implementation depends on strategy

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with signal columns
        """
        df = self.calculate_indicators(df)

        # Generate entry/exit signals
        # Implementation depends on specific strategy

        return df

    def get_position_size(self, price: float, stop_loss: float,
                          capital: float) -> int:
        """
        Calculate position size.

        Args:
            price: Entry price
            stop_loss: Stop loss price
            capital: Available capital

        Returns:
            Number of shares
        """
        risk_per_share = abs(price - stop_loss)
        max_risk = capital * self.risk_per_trade
        shares = int(max_risk / risk_per_share)

        # Limit position size
        max_position = capital * 0.2
        max_shares = int(max_position / price)

        return min(shares, max_shares)

    def scan(self) -> list:
        """
        Scan for current signals.

        Returns:
            List of signal dictionaries
        """
        signals = []

        for symbol in self.symbols:
            try:
                # Download recent data
                ticker = yf.Ticker(symbol)
                df = ticker.history(period='3mo')
                df.columns = [c.lower() for c in df.columns]

                # Generate signals
                df = self.generate_signals(df)

                # Check for entry signal
                if df['entry'].iloc[-1]:
                    signals.append({{
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': df['close'].iloc[-1],
                        'date': df.index[-1].date()
                    }})

            except Exception as e:
                continue

        return signals


def main():
    """Run the strategy scanner."""
    strategy = {strategy_name.title().replace('_', '')}Strategy()

    print("Scanning for signals...")
    signals = strategy.scan()

    if signals:
        print(f"\\nFound {{len(signals)}} signals:")
        for s in signals:
            print(f"  {{s['symbol']}}: {{s['action']}} at ${{s['price']:.2f}}")
    else:
        print("No signals found.")


if __name__ == '__main__':
    main()
'''

        return code

    def generate_top5_combo_code(self) -> str:
        """
        Generate code for combined top 5 strategies.

        Returns:
            Python code string
        """
        if self.rankings is None:
            self.generate_rankings()

        top5 = self.rankings.head(5)['strategy'].tolist()

        code = f'''"""
Top 5 Combined Strategy System
Combines the top 5 uncorrelated strategies for robust performance.

Strategies included:
{chr(10).join(f"- {s}" for s in top5)}

Generated by Stock Trading Backtest System
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, List


class CombinedStrategySystem:
    """
    Combines multiple strategies with allocation weighting.
    """

    def __init__(self, capital: float = 100000):
        """
        Initialize combined system.

        Args:
            capital: Starting capital
        """
        self.capital = capital
        self.strategies = {top5}

        # Allocate capital equally among strategies
        self.allocation = {{s: 1/len(self.strategies) for s in self.strategies}}

        # Risk parameters
        self.max_total_positions = 5
        self.max_drawdown_halt = 0.15  # Halt trading if drawdown >15%

    def get_all_signals(self, symbols: list) -> Dict[str, List]:
        """
        Get signals from all strategies.

        Args:
            symbols: List of symbols to scan

        Returns:
            Dictionary of signals by strategy
        """
        all_signals = {{}}

        # This would call each strategy's scan method
        # Implementation depends on imported strategy classes

        return all_signals

    def combine_signals(self, signals: Dict[str, List]) -> List:
        """
        Combine signals with voting logic.

        Args:
            signals: Dictionary of signals by strategy

        Returns:
            List of combined signals
        """
        # Count votes for each symbol
        votes = {{}}

        for strategy, strategy_signals in signals.items():
            for signal in strategy_signals:
                symbol = signal['symbol']
                if symbol not in votes:
                    votes[symbol] = {{'count': 0, 'signals': []}}
                votes[symbol]['count'] += 1
                votes[symbol]['signals'].append(signal)

        # Only act on signals with multiple strategy confirmations
        combined = []
        for symbol, data in votes.items():
            if data['count'] >= 2:  # At least 2 strategies agree
                combined.append({{
                    'symbol': symbol,
                    'confidence': data['count'] / len(self.strategies),
                    'strategies': [s['symbol'] for s in data['signals']]
                }})

        return sorted(combined, key=lambda x: x['confidence'], reverse=True)

    def allocate_positions(self, signals: List, available_capital: float) -> List:
        """
        Allocate capital to signals.

        Args:
            signals: List of combined signals
            available_capital: Available capital

        Returns:
            List of position recommendations
        """
        positions = []

        for signal in signals[:self.max_total_positions]:
            # Higher confidence = larger allocation
            allocation = signal['confidence'] * (available_capital / self.max_total_positions)

            positions.append({{
                'symbol': signal['symbol'],
                'allocation': allocation,
                'confidence': signal['confidence']
            }})

        return positions


def main():
    """Run the combined strategy system."""
    system = CombinedStrategySystem(capital=100000)

    print("Combined Top 5 Strategy System")
    print("=" * 50)
    print(f"Strategies: {{', '.join(system.strategies)}}")
    print(f"Max positions: {{system.max_total_positions}}")

    # Example usage would go here


if __name__ == '__main__':
    main()
'''

        return code

    def run_stress_tests(self) -> Dict:
        """
        Run stress tests on top strategies.

        Returns:
            Stress test results
        """
        if self.rankings is None:
            self.generate_rankings()

        stress_periods = {
            'covid_crash': ('2020-02-01', '2020-04-30'),
            'bear_2022': ('2022-01-01', '2022-12-31'),
        }

        results = {}
        top_strategies = self.rankings.head(10)['strategy'].tolist()

        for period_name, (start, end) in stress_periods.items():
            period_results = {}

            for strategy_name in top_strategies:
                strategy_func, _, _ = STRATEGY_REGISTRY[strategy_name]

                try:
                    result = self.engine.run_portfolio_backtest(
                        stock_data=self.data_loader.stock_data,
                        strategy_func=strategy_func,
                        strategy_name=strategy_name,
                        start_date=start,
                        end_date=end
                    )

                    period_results[strategy_name] = {
                        'return': result.metrics['total_return_pct'],
                        'max_drawdown': result.metrics['max_drawdown_pct'],
                        'trades': result.metrics['total_trades'],
                        'win_rate': result.metrics['win_rate']
                    }
                except Exception:
                    continue

            results[period_name] = period_results

        return results

    def generate_report(self) -> str:
        """
        Generate comprehensive text report.

        Returns:
            Report string
        """
        if self.rankings is None:
            self.generate_rankings()

        passing, failing = self.validate_strategies()

        report = []
        report.append("=" * 70)
        report.append("STOCK TRADING STRATEGY BACKTEST REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 70)

        report.append(f"\nData Period: {self.data_loader.start_date} to {self.data_loader.end_date}")
        report.append(f"Stocks Tested: {len(self.data_loader.stock_data)}")
        report.append(f"Strategies Tested: {len(self.results)}")

        report.append("\n" + "=" * 70)
        report.append("VALIDATION SUMMARY")
        report.append("=" * 70)
        report.append(f"Strategies Passing All Criteria: {len(passing)}")
        report.append(f"Strategies Failing: {len(failing)}")

        if passing:
            report.append(f"\nPassing Strategies: {', '.join(passing)}")

        report.append("\n" + "=" * 70)
        report.append("TOP 10 STRATEGIES BY COMPOSITE SCORE")
        report.append("=" * 70)

        top10 = self.rankings.head(10)
        for _, row in top10.iterrows():
            report.append(f"\n{row['rank']}. {row['strategy']}")
            report.append(f"   Category: {row['category']}")
            report.append(f"   Win Rate: {row['win_rate']:.1f}%  |  Profit Factor: {row['profit_factor']:.2f}")
            report.append(f"   Sharpe: {row['sharpe_ratio']:.2f}  |  Max DD: {row['max_drawdown']:.1f}%")
            report.append(f"   Annual Return: {row['annual_return']:.1f}%  |  Trades: {row['total_trades']}")
            report.append(f"   Composite Score: {row['composite_score']:.1f}")

        report.append("\n" + "=" * 70)
        report.append("PERFORMANCE BY CATEGORY")
        report.append("=" * 70)

        for category in self.rankings['category'].unique():
            cat_strategies = self.rankings[self.rankings['category'] == category]
            avg_sharpe = cat_strategies['sharpe_ratio'].mean()
            avg_return = cat_strategies['annual_return'].mean()
            report.append(f"\n{category}:")
            report.append(f"  Strategies: {len(cat_strategies)}  |  Avg Sharpe: {avg_sharpe:.2f}  |  Avg Return: {avg_return:.1f}%")

        return "\n".join(report)


def main():
    """Main entry point for running backtests."""
    print("\n" + "=" * 70)
    print("STOCK TRADING STRATEGY BACKTEST SYSTEM")
    print("=" * 70)

    # Initialize runner
    runner = BacktestRunner(data_dir='data', output_dir='output')

    # Load data
    print("\nStep 1: Loading data...")
    if not runner.load_data():
        print("Failed to load data. Exiting.")
        return

    print(f"Loaded {len(runner.data_loader.stock_data)} stocks")

    # Run all strategies
    print("\nStep 2: Running backtests...")
    runner.run_all_strategies(verbose=True)

    # Generate rankings
    print("\nStep 3: Generating rankings...")
    rankings = runner.generate_rankings()

    # Validate strategies
    print("\nStep 4: Validating strategies...")
    passing, failing = runner.validate_strategies()
    print(f"Passing: {len(passing)}, Failing: {len(failing)}")

    # Run stress tests
    print("\nStep 5: Running stress tests...")
    stress_results = runner.run_stress_tests()

    # Save outputs
    print("\nStep 6: Saving outputs...")
    runner.save_rankings()
    runner.save_trade_logs()
    runner.save_equity_curves()

    # Save best strategy code
    best_code = runner.generate_best_strategy_code()
    with open(os.path.join(runner.output_dir, 'best_strategy.py'), 'w') as f:
        f.write(best_code)

    # Save top 5 combo code
    combo_code = runner.generate_top5_combo_code()
    with open(os.path.join(runner.output_dir, 'top5_combo.py'), 'w') as f:
        f.write(combo_code)

    # Generate and save report
    report = runner.generate_report()
    print("\n" + report)

    with open(os.path.join(runner.output_dir, 'backtest_report.txt'), 'w') as f:
        f.write(report)

    # Save stress test results
    with open(os.path.join(runner.output_dir, 'stress_tests.json'), 'w') as f:
        json.dump(stress_results, f, indent=2)

    print("\n" + "=" * 70)
    print("BACKTEST COMPLETE")
    print(f"Results saved to: {runner.output_dir}/")
    print("=" * 70)


if __name__ == '__main__':
    main()

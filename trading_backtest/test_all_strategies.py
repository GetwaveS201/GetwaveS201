"""
Test Runner for Stock Trading Backtest System
Uses synthetic data when yfinance is unavailable.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

warnings.filterwarnings('ignore')

# Add trading_backtest to path
sys.path.insert(0, '/home/user/GetwaveS201/trading_backtest')

from indicators import TechnicalIndicators as ti
from strategies import STRATEGY_REGISTRY, get_all_strategies
from backtest_engine import BacktestEngine, BacktestConfig, BacktestResults, validate_strategy


def generate_synthetic_stock_data(symbol: str, days: int = 2520,
                                   start_price: float = 100.0,
                                   volatility: float = 0.02,
                                   trend: float = 0.0003) -> pd.DataFrame:
    """
    Generate realistic synthetic stock data.

    Args:
        symbol: Stock symbol (used to seed randomness for consistency)
        days: Number of trading days (2520 ~ 10 years)
        start_price: Starting price
        volatility: Daily volatility
        trend: Daily trend (drift)

    Returns:
        DataFrame with OHLCV data
    """
    # Seed based on symbol for reproducibility
    seed = sum(ord(c) for c in symbol)
    np.random.seed(seed)

    # Generate dates (business days only)
    start_date = datetime(2015, 1, 2)
    dates = pd.bdate_range(start=start_date, periods=days)

    # Generate returns with trend and volatility
    returns = np.random.normal(trend, volatility, days)

    # Add some regime changes (occasional high volatility periods)
    for i in range(5):
        start_idx = np.random.randint(0, days - 60)
        returns[start_idx:start_idx + 60] *= 2  # Higher vol period

    # Generate close prices
    close = start_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close
    daily_range = close * volatility * 1.5

    high = close + np.abs(np.random.normal(0, 1, days)) * daily_range * 0.5
    low = close - np.abs(np.random.normal(0, 1, days)) * daily_range * 0.5

    # Ensure low <= close <= high
    low = np.minimum(low, close * 0.995)
    high = np.maximum(high, close * 1.005)

    # Generate open (between previous close and today's range)
    open_prices = np.zeros(days)
    open_prices[0] = start_price
    for i in range(1, days):
        gap = np.random.normal(0, volatility * 0.5)
        open_prices[i] = close[i-1] * (1 + gap)
        open_prices[i] = np.clip(open_prices[i], low[i], high[i])

    # Generate volume (with some correlation to price moves)
    base_volume = 10_000_000
    volume = base_volume * (1 + np.abs(returns) * 10) * np.random.uniform(0.5, 1.5, days)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume.astype(int)
    }, index=dates)

    return df


def generate_stock_universe(num_stocks: int = 50) -> Dict[str, pd.DataFrame]:
    """Generate synthetic data for multiple stocks."""

    # Core symbols
    symbols = [
        'SPY', 'QQQ', 'IWM',  # ETFs
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
        'JPM', 'V', 'MA', 'UNH', 'JNJ', 'PG', 'HD', 'DIS',
        'NFLX', 'ADBE', 'CRM', 'AMD', 'INTC', 'CSCO',
        'BA', 'CAT', 'GS', 'MS', 'WMT', 'COST', 'MCD',
        'XOM', 'CVX', 'PFE', 'MRK', 'ABBV', 'TMO', 'LLY',
        'NEE', 'DUK', 'SO', 'VZ', 'T', 'CMCSA',
        'BRK-B', 'BLK', 'SCHW', 'USB', 'PNC', 'C', 'BAC'
    ][:num_stocks]

    stock_data = {}

    print(f"Generating synthetic data for {len(symbols)} stocks...")

    for i, symbol in enumerate(symbols):
        # Vary parameters by symbol type
        if symbol in ['SPY', 'QQQ', 'IWM']:
            vol = 0.012
            trend = 0.0004
        elif symbol in ['TSLA', 'NVDA', 'AMD']:
            vol = 0.035
            trend = 0.0006
        else:
            vol = 0.02 + np.random.uniform(-0.005, 0.01)
            trend = 0.0003 + np.random.uniform(-0.0002, 0.0003)

        stock_data[symbol] = generate_synthetic_stock_data(
            symbol, days=2520, volatility=vol, trend=trend
        )

    return stock_data


def run_strategy_test(strategy_name: str, strategy_func, stock_data: Dict[str, pd.DataFrame],
                      engine: BacktestEngine) -> BacktestResults:
    """Run backtest for a single strategy."""
    return engine.run_portfolio_backtest(
        stock_data=stock_data,
        strategy_func=strategy_func,
        strategy_name=strategy_name,
        start_date='2015-01-01',
        end_date='2025-01-01'
    )


def main():
    """Run comprehensive strategy testing."""

    print("=" * 70)
    print("STOCK TRADING STRATEGY BACKTEST - COMPREHENSIVE TEST")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Generate synthetic data
    print("Step 1: Generating synthetic stock data...")
    stock_data = generate_stock_universe(num_stocks=40)
    print(f"  Generated data for {len(stock_data)} stocks")
    print(f"  Date range: {list(stock_data.values())[0].index[0].date()} to {list(stock_data.values())[0].index[-1].date()}")
    print(f"  Trading days: {len(list(stock_data.values())[0])}")

    # Initialize backtest engine
    config = BacktestConfig(
        initial_capital=100_000,
        commission_per_trade=1.0,
        slippage_pct=0.0005,
        max_positions=5,
        position_size_pct=0.02
    )
    engine = BacktestEngine(config)

    # Get all strategies
    strategies = get_all_strategies()

    print(f"\nStep 2: Testing {len(strategies)} strategies...")
    print("-" * 70)

    results = {}

    for i, (name, (func, category, desc)) in enumerate(strategies.items(), 1):
        print(f"\n[{i:2}/{len(strategies)}] {name}")
        print(f"    Category: {category}")

        try:
            result = run_strategy_test(name, func, stock_data, engine)
            results[name] = result

            m = result.metrics
            print(f"    Trades: {m['total_trades']:5d} | Win: {m['win_rate']:5.1f}% | "
                  f"PF: {m['profit_factor']:5.2f} | Sharpe: {m['sharpe_ratio']:6.2f} | "
                  f"DD: {m['max_drawdown_pct']:5.1f}%")

        except Exception as e:
            print(f"    ERROR: {str(e)[:60]}")
            continue

    # Generate rankings
    print("\n" + "=" * 70)
    print("Step 3: STRATEGY RANKINGS")
    print("=" * 70)

    records = []
    for name, result in results.items():
        m = result.metrics
        _, category, description = STRATEGY_REGISTRY[name]

        # Calculate composite score
        sharpe_score = min(m['sharpe_ratio'] / 2.0, 1.0) if m['sharpe_ratio'] > 0 else 0
        pf_score = min(m['profit_factor'] / 3.0, 1.0) if m['profit_factor'] > 0 else 0
        win_score = m['win_rate'] / 100
        dd_score = max(0, 1 - m['max_drawdown_pct'] / 50)
        trade_score = min(m['total_trades'] / 500, 1.0)

        composite = (
            sharpe_score * 0.30 +
            pf_score * 0.25 +
            win_score * 0.20 +
            dd_score * 0.15 +
            trade_score * 0.10
        ) * 100

        records.append({
            'strategy': name,
            'category': category,
            'trades': m['total_trades'],
            'win_rate': m['win_rate'],
            'profit_factor': m['profit_factor'],
            'sharpe_ratio': m['sharpe_ratio'],
            'sortino_ratio': m['sortino_ratio'],
            'max_drawdown': m['max_drawdown_pct'],
            'annual_return': m['annual_return_pct'],
            'total_return': m['total_return_pct'],
            'calmar_ratio': m['calmar_ratio'],
            'composite_score': composite
        })

    df = pd.DataFrame(records)
    df = df.sort_values('composite_score', ascending=False)
    df['rank'] = range(1, len(df) + 1)

    # Print top 10
    print("\nTOP 10 STRATEGIES BY COMPOSITE SCORE:")
    print("-" * 70)
    print(f"{'Rank':<5} {'Strategy':<25} {'Win%':<7} {'PF':<7} {'Sharpe':<8} {'DD%':<7} {'Score':<7}")
    print("-" * 70)

    for _, row in df.head(10).iterrows():
        print(f"{row['rank']:<5} {row['strategy']:<25} {row['win_rate']:>5.1f}% "
              f"{row['profit_factor']:>6.2f} {row['sharpe_ratio']:>7.2f} "
              f"{row['max_drawdown']:>5.1f}% {row['composite_score']:>6.1f}")

    # Validation
    print("\n" + "=" * 70)
    print("Step 4: VALIDATION RESULTS")
    print("=" * 70)

    passing = []
    failing = []

    for name, result in results.items():
        m = result.metrics
        passed = True
        failures = []

        if m['win_rate'] < 42:
            passed = False
            failures.append(f"Win rate {m['win_rate']:.1f}% < 42%")
        if m['profit_factor'] < 1.5:
            passed = False
            failures.append(f"PF {m['profit_factor']:.2f} < 1.5")
        if m['sharpe_ratio'] < 0.7:
            passed = False
            failures.append(f"Sharpe {m['sharpe_ratio']:.2f} < 0.7")
        if m['max_drawdown_pct'] > 30:
            passed = False
            failures.append(f"DD {m['max_drawdown_pct']:.1f}% > 30%")
        if m['total_trades'] < 100:  # Reduced for synthetic data
            passed = False
            failures.append(f"Trades {m['total_trades']} < 100")

        if passed:
            passing.append(name)
        else:
            failing.append((name, failures))

    print(f"\nStrategies PASSING all criteria: {len(passing)}")
    if passing:
        for s in passing:
            print(f"  ✓ {s}")

    print(f"\nStrategies FAILING criteria: {len(failing)}")
    for name, reasons in failing[:10]:  # Show first 10
        print(f"  ✗ {name}: {', '.join(reasons[:2])}")

    # Best strategy details
    print("\n" + "=" * 70)
    print("BEST STRATEGY ANALYSIS")
    print("=" * 70)

    best = df.iloc[0]
    best_name = best['strategy']
    best_result = results[best_name]
    _, best_category, best_desc = STRATEGY_REGISTRY[best_name]

    print(f"\n🏆 WINNER: {best_name}")
    print(f"   Category: {best_category}")
    print(f"   Description: {best_desc}")
    print()
    print("   Performance Metrics:")
    print(f"   ├── Total Trades:     {best_result.metrics['total_trades']}")
    print(f"   ├── Win Rate:         {best_result.metrics['win_rate']:.1f}%")
    print(f"   ├── Profit Factor:    {best_result.metrics['profit_factor']:.2f}")
    print(f"   ├── Sharpe Ratio:     {best_result.metrics['sharpe_ratio']:.2f}")
    print(f"   ├── Sortino Ratio:    {best_result.metrics['sortino_ratio']:.2f}")
    print(f"   ├── Max Drawdown:     {best_result.metrics['max_drawdown_pct']:.1f}%")
    print(f"   ├── Annual Return:    {best_result.metrics['annual_return_pct']:.1f}%")
    print(f"   ├── Total Return:     {best_result.metrics['total_return_pct']:.1f}%")
    print(f"   ├── Calmar Ratio:     {best_result.metrics['calmar_ratio']:.2f}")
    print(f"   └── Composite Score:  {best['composite_score']:.1f}")

    # Top 5 by different metrics
    print("\n" + "=" * 70)
    print("TOP 5 BY DIFFERENT METRICS")
    print("=" * 70)

    print("\nBy Sharpe Ratio:")
    for _, row in df.nlargest(5, 'sharpe_ratio').iterrows():
        print(f"  {row['strategy']:<25} Sharpe: {row['sharpe_ratio']:.2f}")

    print("\nBy Profit Factor:")
    for _, row in df.nlargest(5, 'profit_factor').iterrows():
        print(f"  {row['strategy']:<25} PF: {row['profit_factor']:.2f}")

    print("\nBy Win Rate:")
    for _, row in df.nlargest(5, 'win_rate').iterrows():
        print(f"  {row['strategy']:<25} Win: {row['win_rate']:.1f}%")

    print("\nBy Lowest Drawdown:")
    for _, row in df.nsmallest(5, 'max_drawdown').iterrows():
        print(f"  {row['strategy']:<25} DD: {row['max_drawdown']:.1f}%")

    # Performance by category
    print("\n" + "=" * 70)
    print("PERFORMANCE BY CATEGORY")
    print("=" * 70)

    category_stats = df.groupby('category').agg({
        'sharpe_ratio': 'mean',
        'profit_factor': 'mean',
        'win_rate': 'mean',
        'max_drawdown': 'mean',
        'composite_score': 'mean'
    }).round(2)

    category_stats = category_stats.sort_values('composite_score', ascending=False)

    print(f"\n{'Category':<20} {'Sharpe':<8} {'PF':<8} {'Win%':<8} {'DD%':<8} {'Score':<8}")
    print("-" * 60)
    for cat, row in category_stats.iterrows():
        print(f"{cat:<20} {row['sharpe_ratio']:<8.2f} {row['profit_factor']:<8.2f} "
              f"{row['win_rate']:<8.1f} {row['max_drawdown']:<8.1f} {row['composite_score']:<8.1f}")

    # Save results
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)

    output_dir = '/home/user/GetwaveS201/trading_backtest/output'
    os.makedirs(output_dir, exist_ok=True)

    # Save rankings
    df.to_csv(f'{output_dir}/strategy_rankings.csv', index=False)
    print(f"  ✓ Rankings saved to {output_dir}/strategy_rankings.csv")

    # Save detailed results
    detailed = []
    for name, result in results.items():
        m = result.metrics
        _, cat, desc = STRATEGY_REGISTRY[name]
        detailed.append({
            'strategy': name,
            'category': cat,
            'description': desc,
            **{k: v for k, v in m.items() if k != 'yearly_returns'}
        })

    pd.DataFrame(detailed).to_csv(f'{output_dir}/strategy_details.csv', index=False)
    print(f"  ✓ Details saved to {output_dir}/strategy_details.csv")

    print("\n" + "=" * 70)
    print(f"BACKTEST COMPLETE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    return df, results


if __name__ == '__main__':
    rankings, results = main()

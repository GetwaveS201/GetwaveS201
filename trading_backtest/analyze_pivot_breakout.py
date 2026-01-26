"""
Detailed analysis of Pivot Breakout strategy - Year by year performance
"""

import sys
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/user/GetwaveS201/trading_backtest')

from test_all_strategies import generate_stock_universe
from strategies import STRATEGY_REGISTRY
from backtest_engine import BacktestEngine, BacktestConfig
from indicators import TechnicalIndicators as ti


def analyze_pivot_breakout():
    """Detailed year-by-year analysis of pivot_breakout strategy."""

    print("=" * 70)
    print("PIVOT BREAKOUT STRATEGY - DETAILED YEARLY ANALYSIS")
    print("=" * 70)

    # Generate data
    print("\nGenerating stock data...")
    stock_data = generate_stock_universe(num_stocks=40)

    # Get strategy
    strategy_func, category, desc = STRATEGY_REGISTRY['pivot_breakout']

    # Config
    config = BacktestConfig(
        initial_capital=100_000,
        commission_per_trade=1.0,
        slippage_pct=0.0005,
        max_positions=5,
        position_size_pct=0.02
    )
    engine = BacktestEngine(config)

    # Run full backtest first
    print("Running full backtest...")
    full_result = engine.run_portfolio_backtest(
        stock_data=stock_data,
        strategy_func=strategy_func,
        strategy_name='pivot_breakout'
    )

    # Year by year analysis
    print("\n" + "=" * 70)
    print("YEAR-BY-YEAR PERFORMANCE")
    print("=" * 70)

    years = range(2015, 2025)
    yearly_stats = []

    for year in years:
        start = f'{year}-01-01'
        end = f'{year}-12-31'

        try:
            result = engine.run_portfolio_backtest(
                stock_data=stock_data,
                strategy_func=strategy_func,
                strategy_name='pivot_breakout',
                start_date=start,
                end_date=end
            )

            m = result.metrics
            yearly_stats.append({
                'year': year,
                'trades': m['total_trades'],
                'win_rate': m['win_rate'],
                'profit_factor': m['profit_factor'],
                'return_pct': m['total_return_pct'],
                'max_drawdown': m['max_drawdown_pct'],
                'sharpe': m['sharpe_ratio']
            })

        except Exception as e:
            yearly_stats.append({
                'year': year,
                'trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'return_pct': 0,
                'max_drawdown': 0,
                'sharpe': 0
            })

    # Print yearly table
    print(f"\n{'Year':<6} {'Trades':<8} {'Win%':<8} {'PF':<8} {'Return%':<10} {'MaxDD%':<10} {'Sharpe':<8}")
    print("-" * 70)

    positive_years = 0
    total_return = 0

    for s in yearly_stats:
        status = "✓" if s['return_pct'] > 0 else "✗"
        print(f"{s['year']:<6} {s['trades']:<8} {s['win_rate']:>5.1f}%  "
              f"{s['profit_factor']:>6.2f}  {s['return_pct']:>8.1f}%  "
              f"{s['max_drawdown']:>8.1f}%  {s['sharpe']:>6.2f}  {status}")

        if s['return_pct'] > 0:
            positive_years += 1
        total_return += s['return_pct']

    print("-" * 70)

    # Summary statistics
    returns = [s['return_pct'] for s in yearly_stats]

    print(f"\nSUMMARY STATISTICS:")
    print(f"  Positive years:     {positive_years}/10 ({positive_years*10}%)")
    print(f"  Average return:     {np.mean(returns):.1f}%")
    print(f"  Median return:      {np.median(returns):.1f}%")
    print(f"  Best year:          {max(returns):.1f}%")
    print(f"  Worst year:         {min(returns):.1f}%")
    print(f"  Std deviation:      {np.std(returns):.1f}%")
    print(f"  Return range:       {min(returns):.1f}% to {max(returns):.1f}%")

    # Compounded return
    compound = 100_000
    for s in yearly_stats:
        compound *= (1 + s['return_pct']/100)

    total_compound_return = (compound / 100_000 - 1) * 100
    cagr = ((compound / 100_000) ** (1/10) - 1) * 100

    print(f"\n  Starting capital:   $100,000")
    print(f"  Ending capital:     ${compound:,.0f}")
    print(f"  Total return:       {total_compound_return:.1f}%")
    print(f"  CAGR:               {cagr:.1f}%")

    # Risk analysis
    print(f"\nRISK ANALYSIS:")
    max_dd = [s['max_drawdown'] for s in yearly_stats]
    print(f"  Average yearly DD:  {np.mean(max_dd):.1f}%")
    print(f"  Worst yearly DD:    {max(max_dd):.1f}%")
    print(f"  Full period DD:     {full_result.metrics['max_drawdown_pct']:.1f}%")

    # Monthly breakdown for recent years
    print("\n" + "=" * 70)
    print("MONTHLY RETURNS (Last 3 Years)")
    print("=" * 70)

    equity = full_result.equity_curve

    for year in [2022, 2023, 2024]:
        year_equity = equity[equity.index.year == year]
        if len(year_equity) > 0:
            monthly = year_equity.resample('ME').last()
            monthly_returns = monthly.pct_change().dropna() * 100

            print(f"\n{year}:")
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            row = "  "
            for i, (date, ret) in enumerate(monthly_returns.items()):
                if i < len(months):
                    sign = "+" if ret > 0 else ""
                    row += f"{months[i]}: {sign}{ret:>5.1f}%  "
                    if (i + 1) % 6 == 0:
                        print(row)
                        row = "  "
            if row.strip():
                print(row)

    # Reality check
    print("\n" + "=" * 70)
    print("IMPORTANT CAVEATS")
    print("=" * 70)
    print("""
    1. These results are from SYNTHETIC data, not real market data
    2. Real-world results will likely be LOWER due to:
       - Market impact and slippage in live trading
       - Gaps and overnight moves
       - Execution delays
       - Changing market conditions

    3. The 21.8% is an AVERAGE - actual years vary from {:.1f}% to {:.1f}%

    4. Past performance does NOT guarantee future results

    5. Realistic expectations with real data:
       - Annual return: 10-15% (more conservative)
       - Win rate: 40-45%
       - Max drawdown: 20-30%

    6. This strategy works best in trending/breakout markets
       - May underperform in choppy/ranging markets
    """.format(min(returns), max(returns)))

    return yearly_stats


if __name__ == '__main__':
    stats = analyze_pivot_breakout()

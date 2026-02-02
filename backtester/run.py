#!/usr/bin/env python3
"""
Main entry point for the backtesting system.

Usage:
    # Run with sample data
    python -m backtester.run --demo

    # Run a specific strategy on a CSV file
    python -m backtester.run --data data/AAPL.csv --strategy sma_crossover

    # Optimize parameters
    python -m backtester.run --data data/AAPL.csv --strategy sma_crossover --optimize

    # Batch test all CSVs in a directory
    python -m backtester.run --data-dir data/ --strategy sma_crossover

    # Custom strategy parameters
    python -m backtester.run --data data/AAPL.csv --strategy sma_crossover \\
        --param fast_period=5 --param slow_period=20
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Type

import pandas as pd

from .data import load_csv, load_directory, validate_and_clean, resample
from .engine import BacktestConfig, BacktestEngine, BacktestResult, Strategy
from .metrics import PerformanceMetrics, compute_metrics
from .optimize import Optimizer, walk_forward_analysis
from .report import generate_full_report, export_trade_log, generate_summary_report
from .strategies import SMACrossover, RSIMeanReversion, DonchianBreakout


# ---------------------------------------------------------------------------
# Strategy registry
# ---------------------------------------------------------------------------

STRATEGY_REGISTRY: Dict[str, Type[Strategy]] = {
    "sma_crossover": SMACrossover,
    "rsi_mean_reversion": RSIMeanReversion,
    "donchian_breakout": DonchianBreakout,
}

# Default optimization grids per strategy
OPTIMIZATION_GRIDS: Dict[str, Dict] = {
    "sma_crossover": {
        "fast_period": [5, 8, 10, 13, 15, 20],
        "slow_period": [20, 30, 40, 50, 60, 80],
    },
    "rsi_mean_reversion": {
        "rsi_period": [7, 10, 14, 21],
        "oversold": [20, 25, 30, 35],
        "overbought": [65, 70, 75, 80],
    },
    "donchian_breakout": {
        "entry_period": [10, 15, 20, 30, 40, 55],
        "exit_period": [5, 7, 10, 15, 20],
    },
}


# ---------------------------------------------------------------------------
# Core run functions
# ---------------------------------------------------------------------------

def run_single(
    data: pd.DataFrame,
    strategy_class: Type[Strategy],
    config: BacktestConfig,
    params: Optional[Dict] = None,
    output_dir: str = "output",
) -> tuple[BacktestResult, PerformanceMetrics]:
    """Run a single backtest and generate reports."""
    strategy = strategy_class(**(params or {}))
    engine = BacktestEngine(config)
    result = engine.run(data, strategy)
    metrics = compute_metrics(result)

    # Print summary to stdout
    print(metrics)

    # Generate all reports
    paths = generate_full_report(result, metrics, output_dir)
    print(f"\nReports saved:")
    for name, path in paths.items():
        if path:
            print(f"  {name}: {path}")

    return result, metrics


def run_batch(
    data_dict: Dict[str, pd.DataFrame],
    strategy_class: Type[Strategy],
    config: BacktestConfig,
    params: Optional[Dict] = None,
    output_dir: str = "output",
) -> Dict[str, tuple[BacktestResult, PerformanceMetrics]]:
    """Run backtest on multiple symbols."""
    results = {}
    all_metrics = []

    for symbol, data in data_dict.items():
        print(f"\n{'='*55}")
        print(f"  Testing: {symbol}")
        print(f"{'='*55}")

        try:
            result, metrics = run_single(
                data, strategy_class, config, params,
                output_dir=os.path.join(output_dir, symbol),
            )
            results[symbol] = (result, metrics)
            all_metrics.append({
                "symbol": symbol,
                "return_pct": metrics.total_return_pct,
                "sharpe": metrics.sharpe_ratio,
                "max_dd": metrics.max_drawdown_pct,
                "win_rate": metrics.win_rate,
                "trades": metrics.total_trades,
                "profit_factor": metrics.profit_factor,
            })
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Print comparison table
    if all_metrics:
        print(f"\n{'='*75}")
        print("  BATCH COMPARISON")
        print(f"{'='*75}")
        df = pd.DataFrame(all_metrics)
        print(df.to_string(index=False))

    return results


def run_optimization(
    data: pd.DataFrame,
    strategy_class: Type[Strategy],
    config: BacktestConfig,
    param_grid: Dict,
    output_dir: str = "output",
    walk_forward: bool = False,
) -> None:
    """Run parameter optimization."""
    print(f"\nOptimizing {strategy_class.__name__}...")
    print(f"Parameter grid: {param_grid}")

    optimizer = Optimizer(strategy_class, param_grid, config)
    opt_result = optimizer.run(data, metric="sharpe_ratio")

    print(opt_result)

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, "optimization_results.csv")
    opt_result.results_df.to_csv(results_path, index=False)
    print(f"\nDetailed results: {results_path}")

    # Generate surface plot if 2 params
    param_names = list(param_grid.keys())
    if len(param_names) == 2:
        from .visualize import plot_optimization_surface
        import numpy as np

        p1, p2 = param_names
        v1 = list(param_grid[p1])
        v2 = list(param_grid[p2])

        df = opt_result.results_df
        metric_key = "sharpe_ratio_full"

        if metric_key in df.columns:
            matrix = np.full((len(v1), len(v2)), np.nan)
            for _, row in df.iterrows():
                try:
                    i = v1.index(row[p1])
                    j = v2.index(row[p2])
                    matrix[i, j] = row[metric_key]
                except (ValueError, KeyError):
                    continue

            path = plot_optimization_surface(
                p1, p2, v1, v2, matrix,
                metric_name="Sharpe Ratio",
                output_dir=output_dir,
            )
            if path:
                print(f"Surface plot: {path}")

    # Run best params on full data
    print(f"\nBest parameters: {opt_result.best_params}")
    print(f"Running full backtest with best params...")
    run_single(data, strategy_class, config, opt_result.best_params, output_dir)

    # Walk-forward analysis
    if walk_forward:
        print(f"\nRunning walk-forward analysis (5 splits)...")
        wf_result = walk_forward_analysis(
            strategy_class, data, param_grid, config,
            n_splits=5, metric="sharpe_ratio",
        )
        print(f"\nWalk-Forward Results:")
        if "error" not in wf_result:
            for split in wf_result["splits"]:
                print(f"  Split {split['split']}: "
                      f"test_return={split['test_return_pct']:+.2f}%, "
                      f"params={split['best_params']}")
            print(f"  Avg test return: {wf_result['avg_test_return_pct']:+.2f}%")
            print(f"  Consistency: {wf_result['consistency']:.0f}% profitable splits")
        else:
            print(f"  {wf_result['error']}")


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

def run_demo(output_dir: str = "output") -> None:
    """Run a complete demo with sample data and all three strategies."""
    from .sample_data import save_sample_data

    print("=" * 65)
    print("  BACKTESTING SYSTEM - DEMO MODE")
    print("=" * 65)

    # Generate sample data
    print("\n[1] Generating sample data...")
    data_dir = os.path.join(output_dir, "demo_data")
    paths = save_sample_data(data_dir, symbols=2, days=500, seed=42)

    config = BacktestConfig(
        initial_capital=100_000,
        commission_pct=0.001,
        slippage_pct=0.0005,
    )

    # Load first symbol
    data, report = validate_and_clean(load_csv(paths[0]))
    print(report)

    # Test each strategy
    strategies = [
        ("SMA Crossover", SMACrossover, {"fast_period": 10, "slow_period": 30}),
        ("RSI Mean Reversion", RSIMeanReversion, {"rsi_period": 14, "oversold": 30, "overbought": 70}),
        ("Donchian Breakout", DonchianBreakout, {"entry_period": 20, "exit_period": 10}),
    ]

    for name, cls, params in strategies:
        print(f"\n[Strategy: {name}]")
        run_single(data, cls, config, params, os.path.join(output_dir, "demo", name.replace(" ", "_")))

    # Quick optimization demo on SMA
    print("\n[2] Running optimization demo (SMA Crossover)...")
    small_grid = {
        "fast_period": [5, 10, 15],
        "slow_period": [25, 40, 55],
    }
    run_optimization(data, SMACrossover, config, small_grid,
                     os.path.join(output_dir, "demo", "optimization"))

    # Batch test
    print("\n[3] Running batch test on all symbols...")
    all_data = load_directory(data_dir, clean=True)
    run_batch(all_data, SMACrossover, config, {"fast_period": 10, "slow_period": 30},
              os.path.join(output_dir, "demo", "batch"))

    print(f"\n{'='*65}")
    print(f"  Demo complete. All outputs saved to: {output_dir}/demo/")
    print(f"{'='*65}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trading Strategy Backtesting System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Data source
    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument("--data", type=str, help="Path to OHLCV CSV file")
    data_group.add_argument("--data-dir", type=str, help="Directory of CSV files for batch testing")
    data_group.add_argument("--demo", action="store_true", help="Run demo with sample data")

    # Strategy
    parser.add_argument(
        "--strategy", type=str, choices=list(STRATEGY_REGISTRY.keys()),
        default="sma_crossover",
        help="Strategy to use (default: sma_crossover)",
    )
    parser.add_argument(
        "--param", action="append", default=[],
        help="Strategy parameter as key=value (repeatable)",
    )

    # Timeframe
    parser.add_argument("--timeframe", type=str, default=None,
                        help="Resample data to timeframe (e.g. '1d', '4h', '1w')")

    # Config
    parser.add_argument("--capital", type=float, default=100_000, help="Initial capital")
    parser.add_argument("--commission", type=float, default=0.001, help="Commission rate")
    parser.add_argument("--slippage", type=float, default=0.0005, help="Slippage rate")
    parser.add_argument("--position-size", type=float, default=1.0, help="Position size (fraction of equity)")
    parser.add_argument("--no-short", action="store_true", help="Disable short selling")

    # Optimization
    parser.add_argument("--optimize", action="store_true", help="Run parameter optimization")
    parser.add_argument("--walk-forward", action="store_true", help="Include walk-forward analysis")

    # Output
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    return parser.parse_args()


def main():
    args = parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    # Demo mode
    if args.demo:
        run_demo(args.output)
        return

    # Build config
    config = BacktestConfig(
        initial_capital=args.capital,
        commission_pct=args.commission,
        slippage_pct=args.slippage,
        position_size_pct=args.position_size,
        allow_short=not args.no_short,
    )

    # Parse strategy params
    strategy_params = {}
    for p in args.param:
        key, val = p.split("=", 1)
        # Try to parse as number
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                if val.lower() in ("true", "false"):
                    val = val.lower() == "true"
        strategy_params[key] = val

    strategy_class = STRATEGY_REGISTRY[args.strategy]

    # Single file or batch
    if args.data:
        data = load_csv(args.data)
        data, report = validate_and_clean(data)
        print(report)

        if args.timeframe:
            data = resample(data, args.timeframe)
            print(f"Resampled to {args.timeframe}: {len(data)} bars")

        if args.optimize:
            grid = OPTIMIZATION_GRIDS.get(args.strategy, {})
            run_optimization(data, strategy_class, config, grid,
                             args.output, args.walk_forward)
        else:
            run_single(data, strategy_class, config, strategy_params, args.output)

    elif args.data_dir:
        all_data = load_directory(args.data_dir, clean=True)
        if args.timeframe:
            all_data = {k: resample(v, args.timeframe) for k, v in all_data.items()}
        run_batch(all_data, strategy_class, config, strategy_params, args.output)

    else:
        print("No data source specified. Use --data, --data-dir, or --demo.")
        print("Run with --help for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()

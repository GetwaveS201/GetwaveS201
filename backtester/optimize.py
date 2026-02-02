"""
Parameter optimization module.

Systematic parameter search with overfitting detection.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

import numpy as np
import pandas as pd

from .engine import BacktestConfig, BacktestEngine, BacktestResult, Strategy
from .metrics import PerformanceMetrics, compute_metrics

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Optimization result
# ---------------------------------------------------------------------------

@dataclass
class OptimizationResult:
    """Results of a parameter optimization run."""

    all_results: List[Dict[str, Any]] = field(default_factory=list)
    best_params: Dict[str, Any] = field(default_factory=dict)
    best_metric: float = 0.0
    metric_name: str = ""
    overfitting_score: float = 0.0
    stability_score: float = 0.0
    warnings: List[str] = field(default_factory=list)

    @property
    def results_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.all_results)

    def __str__(self) -> str:
        lines = [
            "=" * 55,
            "  OPTIMIZATION RESULTS",
            "=" * 55,
            f"  Metric: {self.metric_name}",
            f"  Best value: {self.best_metric:.4f}",
            f"  Best params: {self.best_params}",
            f"  Combinations tested: {len(self.all_results)}",
            f"  Overfitting risk: {self.overfitting_score:.1f}% {'⚠ HIGH' if self.overfitting_score > 60 else ''}",
            f"  Stability score: {self.stability_score:.1f}%",
        ]
        for w in self.warnings:
            lines.append(f"  WARNING: {w}")
        lines.append("=" * 55)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------

class Optimizer:
    """Grid-search parameter optimizer with overfitting detection.

    Usage::

        opt = Optimizer(
            strategy_class=MyStrategy,
            param_grid={"fast_period": range(5, 30, 5), "slow_period": range(20, 60, 10)},
            config=BacktestConfig(),
        )
        result = opt.run(data, metric="sharpe_ratio")
    """

    def __init__(
        self,
        strategy_class: Type[Strategy],
        param_grid: Dict[str, Any],
        config: Optional[BacktestConfig] = None,
    ):
        self.strategy_class = strategy_class
        self.param_grid = param_grid
        self.config = config or BacktestConfig()

    def run(
        self,
        data: pd.DataFrame,
        metric: str = "sharpe_ratio",
        higher_is_better: bool = True,
        in_sample_pct: float = 0.7,
    ) -> OptimizationResult:
        """Run exhaustive grid search.

        Parameters
        ----------
        data : OHLCV DataFrame
        metric : attribute name from PerformanceMetrics to optimize
        higher_is_better : whether larger metric values are better
        in_sample_pct : fraction of data for in-sample (rest = out-of-sample)
        """
        # Generate all parameter combinations
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(itertools.product(*param_values))

        total = len(combinations)
        logger.info(f"Optimizer: testing {total} parameter combinations")

        # Split data for overfitting detection
        split_idx = int(len(data) * in_sample_pct)
        data_is = data.iloc[:split_idx]
        data_oos = data.iloc[split_idx:]

        engine = BacktestEngine(self.config)
        all_results: List[Dict[str, Any]] = []
        is_metrics_list: List[float] = []
        oos_metrics_list: List[float] = []

        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))

            # Skip invalid combinations (e.g., fast > slow for MA crossovers)
            if not self._validate_params(params):
                continue

            try:
                # In-sample
                strategy_is = self.strategy_class(**params)
                result_is = engine.run(data_is, strategy_is)
                metrics_is = compute_metrics(result_is)
                is_value = getattr(metrics_is, metric, 0.0)

                # Out-of-sample
                strategy_oos = self.strategy_class(**params)
                result_oos = engine.run(data_oos, strategy_oos)
                metrics_oos = compute_metrics(result_oos)
                oos_value = getattr(metrics_oos, metric, 0.0)

                # Full period
                strategy_full = self.strategy_class(**params)
                result_full = engine.run(data, strategy_full)
                metrics_full = compute_metrics(result_full)
                full_value = getattr(metrics_full, metric, 0.0)

                row = {**params}
                row[f"{metric}_is"] = round(is_value, 4)
                row[f"{metric}_oos"] = round(oos_value, 4)
                row[f"{metric}_full"] = round(full_value, 4)
                row["total_return_is"] = round(metrics_is.total_return_pct, 2)
                row["total_return_oos"] = round(metrics_oos.total_return_pct, 2)
                row["total_return_full"] = round(metrics_full.total_return_pct, 2)
                row["total_trades_full"] = metrics_full.total_trades
                row["max_drawdown_full"] = round(metrics_full.max_drawdown_pct, 2)
                row["win_rate_full"] = round(metrics_full.win_rate, 1)

                all_results.append(row)
                is_metrics_list.append(is_value if not np.isnan(is_value) else 0.0)
                oos_metrics_list.append(oos_value if not np.isnan(oos_value) else 0.0)

            except Exception as e:
                logger.warning(f"Combo {params} failed: {e}")
                continue

            if (i + 1) % max(1, total // 10) == 0:
                logger.info(f"  Progress: {i + 1}/{total}")

        if not all_results:
            return OptimizationResult(warnings=["No valid results"])

        # Find best
        opt_result = OptimizationResult(all_results=all_results, metric_name=metric)

        full_key = f"{metric}_full"
        if higher_is_better:
            best_idx = max(range(len(all_results)), key=lambda i: all_results[i].get(full_key, 0))
        else:
            best_idx = min(range(len(all_results)), key=lambda i: all_results[i].get(full_key, 0))

        best_row = all_results[best_idx]
        opt_result.best_params = {k: best_row[k] for k in param_names}
        opt_result.best_metric = best_row[full_key]

        # Overfitting detection
        opt_result.overfitting_score = self._compute_overfitting_score(
            is_metrics_list, oos_metrics_list
        )
        opt_result.stability_score = self._compute_stability_score(all_results, full_key)

        # Warnings
        if opt_result.overfitting_score > 60:
            opt_result.warnings.append(
                f"High overfitting risk ({opt_result.overfitting_score:.0f}%). "
                "In-sample performance diverges significantly from out-of-sample."
            )
        if opt_result.stability_score < 30:
            opt_result.warnings.append(
                f"Low stability ({opt_result.stability_score:.0f}%). "
                "Results are highly sensitive to parameter changes."
            )
        if best_row.get("total_trades_full", 0) < 30:
            opt_result.warnings.append(
                f"Low trade count ({best_row.get('total_trades_full', 0)}). "
                "Results may not be statistically significant."
            )

        return opt_result

    def _validate_params(self, params: Dict[str, Any]) -> bool:
        """Override-friendly param validation. Returns True if valid."""
        # Common check: if both 'fast_*' and 'slow_*' exist, fast < slow
        fast_keys = [k for k in params if k.startswith("fast")]
        slow_keys = [k for k in params if k.startswith("slow")]
        if fast_keys and slow_keys:
            for fk in fast_keys:
                suffix = fk.replace("fast", "")
                sk = "slow" + suffix
                if sk in params:
                    try:
                        if params[fk] >= params[sk]:
                            return False
                    except TypeError:
                        pass
        return True

    @staticmethod
    def _compute_overfitting_score(
        is_metrics: List[float], oos_metrics: List[float]
    ) -> float:
        """Estimate overfitting risk (0-100).

        Compares rank correlation between in-sample and out-of-sample performance.
        Low correlation = high overfitting risk.
        """
        if len(is_metrics) < 3:
            return 50.0  # Not enough data

        is_arr = np.array(is_metrics)
        oos_arr = np.array(oos_metrics)

        # Rank correlation (Spearman)
        is_ranks = _rankdata(is_arr)
        oos_ranks = _rankdata(oos_arr)

        n = len(is_ranks)
        d_sq = np.sum((is_ranks - oos_ranks) ** 2)
        rho = 1 - (6 * d_sq) / (n * (n ** 2 - 1)) if n > 1 else 0

        # Convert: rho=1 -> 0% overfit, rho=-1 -> 100% overfit
        overfit_score = max(0, min(100, (1 - rho) * 50))
        return overfit_score

    @staticmethod
    def _compute_stability_score(
        all_results: List[Dict[str, Any]], metric_key: str
    ) -> float:
        """Estimate stability (0-100).

        High stability = many parameter combos produce decent results.
        """
        values = [r.get(metric_key, 0) for r in all_results]
        if not values:
            return 0.0

        values = np.array(values)
        best = values.max()

        if best <= 0:
            return 0.0

        # Fraction of combos achieving > 50% of best result
        threshold = best * 0.5
        good_count = np.sum(values > threshold)
        stability = (good_count / len(values)) * 100
        return float(stability)


# ---------------------------------------------------------------------------
# Walk-forward analysis
# ---------------------------------------------------------------------------

def walk_forward_analysis(
    strategy_class: Type[Strategy],
    data: pd.DataFrame,
    param_grid: Dict[str, Any],
    config: Optional[BacktestConfig] = None,
    n_splits: int = 5,
    train_pct: float = 0.7,
    metric: str = "sharpe_ratio",
) -> Dict[str, Any]:
    """Run walk-forward optimization.

    Splits data into n_splits windows, optimizes on training portion,
    tests on the remaining portion. This more closely simulates real trading.

    Returns summary dict with per-window and aggregate results.
    """
    config = config or BacktestConfig()
    total_bars = len(data)
    window_size = total_bars // n_splits

    results = []

    for split in range(n_splits):
        start = split * window_size
        end = min(start + window_size, total_bars)
        window_data = data.iloc[start:end]

        if len(window_data) < 50:
            continue

        split_point = int(len(window_data) * train_pct)
        train_data = window_data.iloc[:split_point]
        test_data = window_data.iloc[split_point:]

        if len(train_data) < 30 or len(test_data) < 10:
            continue

        # Optimize on training data
        opt = Optimizer(strategy_class, param_grid, config)
        opt_result = opt.run(train_data, metric=metric, in_sample_pct=1.0)

        if not opt_result.best_params:
            continue

        # Test best params on out-of-sample
        best_strategy = strategy_class(**opt_result.best_params)
        engine = BacktestEngine(config)
        test_result = engine.run(test_data, best_strategy)
        test_metrics = compute_metrics(test_result)

        results.append({
            "split": split + 1,
            "train_start": train_data.index[0],
            "train_end": train_data.index[-1],
            "test_start": test_data.index[0],
            "test_end": test_data.index[-1],
            "best_params": opt_result.best_params,
            f"train_{metric}": opt_result.best_metric,
            f"test_{metric}": getattr(test_metrics, metric, 0),
            "test_return_pct": test_metrics.total_return_pct,
            "test_trades": test_metrics.total_trades,
        })

    # Aggregate
    if results:
        test_metrics_values = [r[f"test_{metric}"] for r in results]
        test_returns = [r["test_return_pct"] for r in results]
        summary = {
            "splits": results,
            f"avg_test_{metric}": np.mean(test_metrics_values),
            "avg_test_return_pct": np.mean(test_returns),
            "consistency": np.sum(np.array(test_returns) > 0) / len(test_returns) * 100,
        }
    else:
        summary = {"splits": [], "error": "No valid splits"}

    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rankdata(arr: np.ndarray) -> np.ndarray:
    """Simple rank implementation (average ties)."""
    sorter = np.argsort(arr)
    ranks = np.empty_like(sorter, dtype=float)
    ranks[sorter] = np.arange(1, len(arr) + 1, dtype=float)
    return ranks

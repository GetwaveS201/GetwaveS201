# Stock Trading Strategy Backtest System

A comprehensive stock trading strategy backtesting system that tests 30+ proven strategies, validates with statistical rigor, and outputs executable trading code.

## Features

- **30 Trading Strategies** across 5 categories:
  - Mean Reversion (6 strategies)
  - Momentum & Trend (8 strategies)
  - Breakout & Volatility (6 strategies)
  - Market Structure (5 strategies)
  - Volume & Money Flow (5 strategies)

- **Comprehensive Backtesting**:
  - 10 years of historical data (2015-2025)
  - 100+ liquid stocks from Russell 1000
  - Realistic execution with slippage and commissions
  - Walk-forward optimization
  - Market regime analysis

- **Risk Management**:
  - Position sizing based on ATR
  - Stop loss and take profit management
  - Portfolio-level risk constraints
  - Sector concentration limits

- **Daily Scanner**:
  - Real-time signal generation
  - Watchlist generation
  - Market context analysis

## Installation

### Requirements

```bash
pip install pandas numpy yfinance matplotlib plotly scikit-learn
```

### Optional (for advanced backtesting)

```bash
pip install pandas-ta vectorbt backtrader
```

## Quick Start

### 1. Run Full Backtest

```bash
python main_backtest.py
```

This will:
1. Download/load stock data
2. Run all 30 strategies
3. Generate rankings and reports
4. Save results to `output/` directory

### 2. Daily Scanner

```bash
python daily_scanner.py
```

Or with custom options:

```bash
python daily_scanner.py --symbols AAPL MSFT GOOGL --strategies rsi_oversold macd_bullish
```

### 3. Test Single Strategy

```python
from data_loader import DataLoader
from strategies import TradingStrategies
from backtest_engine import BacktestEngine, BacktestConfig

# Load data
loader = DataLoader()
loader.download_all_stocks()

# Run backtest
engine = BacktestEngine(BacktestConfig())
signal = TradingStrategies.strategy_01_rsi_oversold(df)
trades = engine.run_backtest(df, signal, 'SPY')
```

## Project Structure

```
trading_backtest/
├── data_loader.py       # Downloads and cleans stock data
├── indicators.py        # Technical indicator calculations
├── strategies.py        # 30 trading strategies
├── backtest_engine.py   # Backtesting engine
├── risk_manager.py      # Position sizing and risk management
├── main_backtest.py     # Main entry point
├── daily_scanner.py     # Daily signal scanner
├── README.md            # This file
├── STRATEGY_RULES.md    # Strategy documentation
├── data/                # Cached data files
└── output/              # Generated reports and results
```

## Output Files

After running `main_backtest.py`:

| File | Description |
|------|-------------|
| `strategy_rankings.csv` | All strategies ranked by performance |
| `trade_log.csv` | Every trade with entry/exit details |
| `equity_curves.csv` | Daily equity values for each strategy |
| `best_strategy.py` | Standalone code for top strategy |
| `top5_combo.py` | Combined top 5 strategy system |
| `backtest_report.txt` | Comprehensive performance report |
| `stress_tests.json` | Results from stress testing |
| `signals_today.txt` | Current trading signals |
| `watchlist.csv` | Watchlist for upcoming setups |

## Strategy Validation Criteria

Strategies must pass ALL criteria:

| Metric | Threshold |
|--------|-----------|
| Win Rate | > 42% |
| Profit Factor | > 1.5 |
| Sharpe Ratio | > 0.7 |
| Max Drawdown | < 30% |
| Minimum Trades | > 200 |
| Positive Years | ≥ 6 of 10 |

Advanced metrics:
- Sortino Ratio > 1.0
- Calmar Ratio > 0.8
- Recovery Factor > 1.5
- Walk-forward Efficiency > 40%

## Risk Management Rules

**Position Level:**
- Max 2% account risk per trade
- Stop loss: 1.5x ATR or 6% max
- Take profit: 2:1 or 3:1 minimum reward/risk

**Portfolio Level:**
- Max 5 simultaneous positions
- Max 40% sector concentration
- Max 10% total portfolio heat

## Backtesting Parameters

```python
BacktestConfig(
    initial_capital=100_000,
    commission_per_trade=1.0,      # $1 per trade
    slippage_pct=0.0005,           # 0.05%
    max_positions=5,
    position_size_pct=0.02,        # 2% risk per trade
    max_risk_pct=0.06,             # 6% max stop
    use_next_day_open=True         # Enter at next day's open
)
```

## Data Requirements

- **Stocks**: SPY, QQQ, IWM + top 100 liquid Russell 1000 stocks
- **Data**: OHLCV + Adjusted Close
- **Additional**: VIX for market regime filtering
- **Filters**:
  - Minimum $5 price
  - $50M daily volume
  - Survivorship bias handling

## Market Regime Analysis

The system classifies market regimes:

| Regime | Conditions |
|--------|------------|
| Bull Market | SPY uptrend, VIX < 20 |
| Bear Market | SPY downtrend, VIX > 25 |
| High Volatility | VIX > 30 |
| Neutral | Everything else |

## Walk-Forward Optimization

```python
# Run walk-forward analysis
from main_backtest import BacktestRunner

runner = BacktestRunner()
runner.load_data()
wf_results = runner.run_walk_forward(
    strategy_name='rsi_oversold',
    train_months=12,
    test_months=3
)
print(f"Walk-forward efficiency: {wf_results['walk_forward_efficiency']:.1f}%")
```

## Stress Testing

Automatic stress tests on:
- COVID crash (Feb-Apr 2020)
- 2022 bear market
- Simulated 50% crash scenarios

## Adding New Strategies

1. Add strategy function to `strategies.py`:

```python
@staticmethod
def strategy_31_my_strategy(df: pd.DataFrame, params: dict = None) -> StrategySignal:
    """My custom strategy."""
    # Calculate indicators
    # Generate entry/exit signals
    return StrategySignal(entry=entry, exit=exit_signal, stop_loss=stop_loss)
```

2. Register in `STRATEGY_REGISTRY`:

```python
'my_strategy': (TradingStrategies.strategy_31_my_strategy, 'Category', 'Description'),
```

## Performance Expectations

Realistic expectations for validated strategies:
- **Annual Return**: 12-20%
- **Win Rate**: 45-55%
- **Max Drawdown**: 18-25%
- **Sharpe Ratio**: 0.8-1.5

## Safety Checks

The system includes:
- ✓ No lookahead bias verification
- ✓ Data quality validation
- ✓ Indicator calculation verification
- ✓ Unrealistic result flagging (>100% annual = likely bug)
- ✓ Minimum trade count requirements
- ✓ Out-of-sample validation

## License

This project is for educational purposes. Use at your own risk. Past performance does not guarantee future results.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Submit a pull request

## Disclaimer

This software is for educational and research purposes only. It is not financial advice. Trading stocks involves risk, and you should never trade with money you cannot afford to lose. Always do your own research and consult with a financial advisor before making investment decisions.

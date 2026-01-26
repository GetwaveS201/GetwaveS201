# Pivot Breakout EA for MetaTrader 5

A fully automated Expert Advisor implementing the Pivot Point Breakout strategy.

## Strategy Rules

| Rule | Description |
|------|-------------|
| **Entry** | Buy when price closes above R1 pivot resistance |
| **Exit** | Close when price drops below pivot point |
| **Stop Loss** | Placed at pivot point level |
| **Take Profit** | Based on Risk:Reward ratio (default 2:1) |

## Installation

1. **Copy the EA file:**
   - Copy `PivotBreakout_EA.mq5` to your MT5 data folder:
   - `C:\Users\[YourName]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Experts\`
   - Or use File → Open Data Folder in MT5

2. **Compile the EA:**
   - Open MetaEditor (F4 in MT5)
   - Open the EA file
   - Press F7 to compile
   - Check for no errors in the log

3. **Attach to Chart:**
   - In MT5, open a chart (recommended: H4 or Daily)
   - Drag the EA from Navigator onto the chart
   - Enable "Allow Algo Trading" in EA settings
   - Click OK

## Input Parameters

### Risk Management
| Parameter | Default | Description |
|-----------|---------|-------------|
| RiskPercent | 2.0 | Risk per trade as % of account |
| RewardRiskRatio | 2.0 | Take profit multiplier (2 = 2:1 R:R) |
| MaxDrawdownPercent | 20.0 | Stop trading if drawdown exceeds this |

### Trade Settings
| Parameter | Default | Description |
|-----------|---------|-------------|
| MagicNumber | 123456 | Unique ID for this EA's trades |
| FixedLotSize | 0.0 | Set >0 to use fixed lots instead of % risk |
| MaxOpenTrades | 1 | Maximum simultaneous positions |
| Slippage | 10 | Max allowed slippage in points |

### Pivot Settings
| Parameter | Default | Description |
|-----------|---------|-------------|
| PivotTimeframe | D1 | Timeframe for pivot calculation |
| UseR2Breakout | false | Use R2 instead of R1 for entry |
| TrailingStopEnabled | true | Enable trailing stop |
| TrailingStopATRMult | 1.5 | Trailing stop distance (ATR multiplier) |

### Time Filter
| Parameter | Default | Description |
|-----------|---------|-------------|
| UseTimeFilter | false | Enable trading hours filter |
| StartHour | 9 | Start trading (server time) |
| EndHour | 17 | Stop trading (server time) |

## Recommended Settings

### Conservative (Lower Risk)
```
RiskPercent = 1.0
RewardRiskRatio = 2.0
MaxOpenTrades = 1
TrailingStopEnabled = true
```

### Moderate
```
RiskPercent = 2.0
RewardRiskRatio = 2.5
MaxOpenTrades = 2
TrailingStopEnabled = true
```

### Aggressive (Higher Risk)
```
RiskPercent = 3.0
RewardRiskRatio = 3.0
MaxOpenTrades = 3
UseR2Breakout = true
```

## Best Pairs/Instruments

The strategy works best on:
- **Forex:** EURUSD, GBPUSD, USDJPY, AUDUSD
- **Indices:** US30, US500, NAS100, GER40
- **Commodities:** XAUUSD (Gold)

## Timeframe Recommendations

| Instrument Type | Chart TF | Pivot TF |
|-----------------|----------|----------|
| Forex | H4 | D1 |
| Indices | H1-H4 | D1 |
| Gold | H4 | D1 |

## Backtesting

1. Open Strategy Tester (Ctrl+R)
2. Select PivotBreakout_EA
3. Set symbol and timeframe
4. Set date range (minimum 1 year)
5. Model: "Every tick based on real ticks" (most accurate)
6. Run test

### Expected Results (Realistic)
| Metric | Range |
|--------|-------|
| Win Rate | 40-48% |
| Profit Factor | 1.1-1.4 |
| Annual Return | 10-20% |
| Max Drawdown | 15-30% |

## Risk Warning

- This EA involves significant risk of loss
- Past performance does not guarantee future results
- Never risk money you cannot afford to lose
- Always test on demo account first
- Monitor the EA regularly

## Troubleshooting

### EA Not Trading
1. Check if "Algo Trading" is enabled (button on toolbar)
2. Verify account has sufficient margin
3. Check if market is open
4. Review Experts tab for error messages

### Compilation Errors
1. Ensure you have the latest MT5 build
2. Check that Trade library files exist in Include folder
3. Try restarting MetaEditor

### Large Drawdown
1. Reduce RiskPercent
2. Enable MaxDrawdownPercent protection
3. Consider using time filter to avoid volatile sessions

## Version History

- v1.00 - Initial release

## License

This EA is provided for educational purposes. Use at your own risk.

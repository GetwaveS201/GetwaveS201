# Trading Strategy Rules Documentation

This document provides plain English explanations of each strategy's entry/exit rules in the backtesting system.

---

## Table of Contents

1. [Mean Reversion Strategies](#mean-reversion-strategies)
2. [Momentum & Trend Strategies](#momentum--trend-strategies)
3. [Breakout & Volatility Strategies](#breakout--volatility-strategies)
4. [Market Structure Strategies](#market-structure-strategies)
5. [Volume & Money Flow Strategies](#volume--money-flow-strategies)

---

## Mean Reversion Strategies

### Strategy 1: RSI Oversold Bounce

**Concept**: Buy when a stock becomes oversold and shows signs of recovery.

**Entry Rules**:
- RSI (14-period) drops below 30
- Wait for the day RSI crosses below 30

**Exit Rules**:
- RSI rises above 50
- Stop loss: 2x ATR below entry

**Rationale**: When a stock becomes oversold (RSI < 30), it often bounces back toward fair value. We exit at RSI 50 (neutral territory).

---

### Strategy 2: Bollinger Band Snapback

**Concept**: Buy when price dips below the lower Bollinger Band and snaps back inside.

**Entry Rules**:
- Previous day: Close was below lower Bollinger Band (20-day, 2 std dev)
- Today: Close is back above lower band

**Exit Rules**:
- Price reaches the middle Bollinger Band
- Stop loss: Below lower band minus 1 ATR
- Take profit: Upper Bollinger Band

**Rationale**: Prices tend to stay within Bollinger Bands 95% of the time. When price dips below, a reversion to the mean is likely.

---

### Strategy 3: Z-Score Reversion

**Concept**: Buy when price is statistically extreme (2+ standard deviations below mean).

**Entry Rules**:
- Price Z-score drops below -2.0 (20-day lookback)
- Entry when Z-score first crosses below -2.0

**Exit Rules**:
- Z-score rises above -0.5 (returning toward mean)
- Stop loss: 1.5x ATR below entry

**Rationale**: Extreme statistical deviations are rarely sustained and tend to revert to average.

---

### Strategy 4: Gap Fade

**Concept**: Buy stocks that gap down significantly on high volume and show reversal.

**Entry Rules**:
- Gap down > 3% (open vs. previous close)
- Volume > 1.5x 20-day average
- Price recovering (close > open for the day)

**Exit Rules**:
- Price reaches previous close (gap filled)
- Stop loss: Day's low minus 1 ATR

**Rationale**: Large gaps often fill during the trading session, especially when caused by overreaction.

---

### Strategy 5: Williams %R Extreme Reversal

**Concept**: Buy when Williams %R shows extreme oversold conditions reversing.

**Entry Rules**:
- Williams %R (14-period) was below -80 (extremely oversold)
- Williams %R crosses back above -80

**Exit Rules**:
- Williams %R crosses above -20 (overbought territory)
- Stop loss: 1.5x ATR below entry

**Rationale**: Williams %R extremes below -80 indicate panic selling, which often precedes a bounce.

---

### Strategy 6: CCI Extreme Reversal

**Concept**: Buy when CCI shows extreme oversold conditions reversing.

**Entry Rules**:
- CCI (20-period) was below -100
- CCI crosses back above -100

**Exit Rules**:
- CCI crosses above 0 (neutral)
- Stop loss: 1.5x ATR below entry

**Rationale**: CCI below -100 indicates significant oversold conditions that often reverse.

---

## Momentum & Trend Strategies

### Strategy 7: EMA Crossover (20/50)

**Concept**: Buy when short-term trend crosses above long-term trend with volume confirmation.

**Entry Rules**:
- EMA 20 crosses above EMA 50
- Volume > 1.2x 20-day average

**Exit Rules**:
- EMA 20 crosses below EMA 50
- Stop loss: Below EMA 50 minus 1 ATR

**Rationale**: Moving average crossovers identify trend changes. Volume confirms conviction.

---

### Strategy 8: MACD Bullish Cross

**Concept**: Buy when MACD line crosses above signal line with positive momentum.

**Entry Rules**:
- MACD line crosses above signal line
- MACD histogram turns positive

**Exit Rules**:
- MACD histogram turns negative
- Stop loss: 2x ATR below entry

**Rationale**: MACD crossovers with histogram confirmation show strong momentum shifts.

---

### Strategy 9: ADX Trend Strength

**Concept**: Trade in the direction of strong trends identified by ADX.

**Entry Rules**:
- ADX > 25 (strong trend present)
- +DI crosses above -DI (bullish direction)

**Exit Rules**:
- +DI crosses below -DI, OR
- ADX falls below 20 (trend weakening)
- Stop loss: 1.5x ATR below entry

**Rationale**: ADX measures trend strength; we only trade when a strong trend is confirmed.

---

### Strategy 10: Supertrend

**Concept**: Follow the Supertrend indicator's direction changes.

**Entry Rules**:
- Supertrend direction changes from bearish (-1) to bullish (+1)

**Exit Rules**:
- Supertrend direction changes to bearish
- Stop loss: Supertrend line itself acts as trailing stop

**Rationale**: Supertrend provides clear trend signals with built-in stop loss levels.

---

### Strategy 11: Donchian Channel Breakout

**Concept**: Buy when price breaks above the 20-day high.

**Entry Rules**:
- Close breaks above 20-day Donchian upper channel

**Exit Rules**:
- Close breaks below 10-day Donchian lower channel
- Stop loss: 10-day low

**Rationale**: Breakouts to new highs indicate strong buying pressure that often continues.

---

### Strategy 12: 52-Week High Breakout

**Concept**: Buy when price makes new 52-week high with strong volume.

**Entry Rules**:
- New 52-week high
- Volume ≥ 2x 20-day average

**Exit Rules**:
- Price drops below 10-day low
- Stop loss: 10-day low

**Rationale**: New highs with volume indicate institutional buying and continued momentum.

---

### Strategy 13: Triple EMA Alignment

**Concept**: Buy when all three EMAs are aligned bullishly.

**Entry Rules**:
- EMA 9 > EMA 21 > EMA 55
- Alignment just occurred (wasn't aligned yesterday)

**Exit Rules**:
- EMA 9 crosses below EMA 21
- Stop loss: Below EMA 55 minus 1 ATR

**Rationale**: When multiple timeframes align, trend strength is confirmed.

---

### Strategy 14: Rate of Change Momentum

**Concept**: Buy stocks showing strong momentum (price change).

**Entry Rules**:
- ROC (10-day) > 10% (price up 10%+ in 10 days)

**Exit Rules**:
- ROC falls below 2%
- Stop loss: 2x ATR below entry

**Rationale**: Strong momentum tends to persist in the short term.

---

## Breakout & Volatility Strategies

### Strategy 15: Consolidation Breakout

**Concept**: Buy when price breaks out of a tight consolidation.

**Entry Rules**:
- Previous 5 days: price range < 5% of closing price
- Today: Close breaks above the 5-day high

**Exit Rules**:
- Price falls below running 10-day max minus 2 ATR
- Stop loss: 5-day low

**Rationale**: Tight consolidations (coiling) often precede explosive moves.

---

### Strategy 16: Volume Breakout

**Concept**: Buy when price surges up on extremely high volume.

**Entry Rules**:
- Volume ≥ 3x 20-day average
- Price up > 2% for the day

**Exit Rules**:
- Volume normalizes (< 1.5x average) and price stalls
- Stop loss: 1.5x ATR below entry

**Rationale**: High volume price increases indicate institutional accumulation.

---

### Strategy 17: ATR Expansion

**Concept**: Buy when volatility expands with bullish price action.

**Entry Rules**:
- ATR increased > 50% over past 3 days
- Price up over the same 3 days

**Exit Rules**:
- ATR contracting AND price falling
- Stop loss: 2x ATR below entry

**Rationale**: Volatility expansion with price gains often precedes trend continuation.

---

### Strategy 18: Bollinger Band Squeeze

**Concept**: Buy when Bollinger Bands squeeze and price breaks upward.

**Entry Rules**:
- Bollinger Bandwidth at 20-day low (squeeze)
- Next day: Bandwidth expanding AND close above middle band

**Exit Rules**:
- Close below middle Bollinger Band
- Stop loss: Lower Bollinger Band

**Rationale**: Bollinger squeezes precede explosive moves; we trade the upside breakout.

---

### Strategy 19: Opening Range Breakout

**Concept**: Buy when price breaks above its opening range.

**Entry Rules**:
- High > (Open + 0.5 x ATR)
- Using daily data approximation

**Exit Rules**:
- Low < (Open - 0.5 x ATR)
- Stop loss: Opening range low

**Rationale**: Early price momentum often sets the direction for the day.

---

### Strategy 20: Pivot Point Breakout

**Concept**: Buy when price breaks above R1 pivot resistance.

**Entry Rules**:
- Close breaks above R1 pivot point

**Exit Rules**:
- Close drops below pivot point
- Stop loss: Pivot point level

**Rationale**: Pivot breakouts indicate strong bullish momentum.

---

## Market Structure Strategies

### Strategy 21: Higher Highs & Higher Lows

**Concept**: Buy when uptrend structure is established.

**Entry Rules**:
- 3+ consecutive higher highs
- 3+ consecutive higher lows
- Structure just established

**Exit Rules**:
- Lower low is formed (breaks structure)
- Stop loss: Recent swing low minus 1 ATR

**Rationale**: Established uptrend structure tends to continue.

---

### Strategy 22: Support Bounce

**Concept**: Buy when price bounces off established support.

**Entry Rules**:
- Price within 2% of 20-day support level
- Green candle (close > open)

**Exit Rules**:
- Close below support level
- Stop loss: Support minus 1 ATR
- Take profit: 20-day resistance level

**Rationale**: Tested support levels often hold, providing low-risk entries.

---

### Strategy 23: Fibonacci Retracement Entry

**Concept**: Buy when price bounces from key Fibonacci level.

**Entry Rules**:
- Price touches 61.8% Fibonacci retracement level
- Green candle showing bounce

**Exit Rules**:
- Price breaks below 78.6% retracement
- Stop loss: 78.6% level
- Take profit: Swing high

**Rationale**: Fibonacci levels act as natural support in uptrends.

---

### Strategy 24: Trendline Retest

**Concept**: Buy when price retests and bounces from trendline.

**Entry Rules**:
- Price within 1% of 20-day EMA (trendline proxy)
- EMA is rising (uptrend)
- Close above EMA

**Exit Rules**:
- Close below EMA
- Stop loss: EMA minus 1 ATR

**Rationale**: Trendline retests offer low-risk entry points in uptrends.

---

### Strategy 25: Inside Bar Breakout

**Concept**: Buy when price breaks out of an inside bar pattern.

**Entry Rules**:
- Yesterday: Inside bar (high < previous high, low > previous low)
- Today: High breaks above mother bar's high

**Exit Rules**:
- Close below inside bar's low
- Stop loss: Mother bar's low

**Rationale**: Inside bars represent consolidation before expansion; breakout shows direction.

---

## Volume & Money Flow Strategies

### Strategy 26: OBV Divergence

**Concept**: Buy when OBV shows bullish divergence (OBV rising while price falling).

**Entry Rules**:
- Price makes lower low
- OBV makes higher low (bullish divergence)

**Exit Rules**:
- OBV breaks below 10-day minimum
- Stop loss: 2x ATR below entry

**Rationale**: Volume precedes price; bullish divergence signals accumulation.

---

### Strategy 27: MFI Reversal

**Concept**: Buy when Money Flow Index reverses from oversold.

**Entry Rules**:
- MFI was below 20 (oversold) in past 5 days
- MFI crosses above 40

**Exit Rules**:
- MFI > 80 (overbought), OR
- MFI crosses below 50
- Stop loss: 1.5x ATR below entry

**Rationale**: MFI combines price and volume; oversold MFI reversals signal buying.

---

### Strategy 28: Chaikin Money Flow Cross

**Concept**: Buy when CMF turns positive, indicating buying pressure.

**Entry Rules**:
- CMF (20-day) crosses above 0

**Exit Rules**:
- CMF crosses below 0
- Stop loss: 1.5x ATR below entry

**Rationale**: Positive CMF indicates more money flowing into the stock than out.

---

### Strategy 29: VWAP Mean Reversion

**Concept**: Buy when price is significantly below VWAP and reversing.

**Entry Rules**:
- Price > 3% below 20-day VWAP
- Price showing recovery (close > yesterday's close)

**Exit Rules**:
- Price returns to VWAP
- Stop loss: 5-day low
- Take profit: VWAP level

**Rationale**: Price tends to revert to VWAP, the volume-weighted fair value.

---

### Strategy 30: Volume Spike Breakout

**Concept**: Buy when unusual volume accompanies a price breakout.

**Entry Rules**:
- Volume ≥ 5x 20-day average
- Price breaks above 10-day high

**Exit Rules**:
- Volume normalizes (< 2x) AND price stagnant
- Stop loss: 2x ATR below entry

**Rationale**: Volume spikes with breakouts indicate institutional activity.

---

## Risk Management Notes

### For All Strategies:

1. **Position Sizing**: Risk max 2% of capital per trade
2. **Stop Loss**: Tighter of strategy stop or 6% max
3. **Take Profit**: Minimum 2:1 reward/risk ratio
4. **Entry**: At next day's open after signal
5. **Max Positions**: 5 concurrent trades
6. **Sector Limit**: Max 40% in any sector

### Market Regime Adjustments:

| Regime | Position Adjustment |
|--------|-------------------|
| Bull Market (VIX < 20) | Normal sizing |
| Elevated Vol (VIX 20-25) | Reduce by 10% |
| High Vol (VIX 25-30) | Reduce by 25% |
| Extreme Vol (VIX > 30) | Reduce by 50% |

---

## Strategy Selection Guidelines

### Best in Bull Markets:
- Momentum strategies (7-14)
- Breakout strategies (15-20)

### Best in Ranging Markets:
- Mean reversion (1-6)
- Support/resistance (22-23)

### Best in High Volatility:
- Volatility strategies (17-18)
- Volume strategies (26-30)

### Most Consistent:
- EMA Crossover (7)
- Supertrend (10)
- Support Bounce (22)

---

*Remember: Past performance does not guarantee future results. Always practice proper risk management.*

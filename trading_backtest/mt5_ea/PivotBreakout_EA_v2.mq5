//+------------------------------------------------------------------+
//|                                        PivotBreakout_EA_v2.mq5   |
//|                          Pivot Point Breakout Strategy - FIXED   |
//+------------------------------------------------------------------+
#property copyright "Trading Backtest System"
#property link      ""
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+
input group "=== Risk Management ==="
input double   RiskPercent = 2.0;           // Risk per trade (%)
input double   RewardRiskRatio = 2.0;       // Reward to Risk ratio
input double   MaxDrawdownPercent = 20.0;   // Max drawdown to stop trading (%)

input group "=== Trade Settings ==="
input int      MagicNumber = 123456;        // Magic number for this EA
input double   FixedLotSize = 0.1;          // Fixed lot size (0 = use risk %)
input int      MaxOpenTrades = 1;           // Max simultaneous trades
input int      Slippage = 30;               // Maximum slippage (points)

input group "=== Pivot Settings ==="
input bool     UseR2Breakout = false;       // Use R2 instead of R1 for entry
input bool     TrailingStopEnabled = true;  // Enable trailing stop
input double   TrailingStopATRMult = 1.5;   // Trailing stop ATR multiplier

input group "=== Entry Settings ==="
input int      EntryTimeframe = 15;         // Entry timeframe (minutes): 5, 15, 60
input bool     RequireCloseAbove = false;   // Require candle CLOSE above R1 (false = any break)
input double   BreakoutBuffer = 0.0;        // Buffer above R1 for entry (points)

input group "=== Time Filter ==="
input bool     UseTimeFilter = false;       // Enable time filter
input int      StartHour = 8;               // Trading start hour
input int      EndHour = 20;                // Trading end hour

input group "=== Display ==="
input bool     ShowPivotLines = true;       // Show pivot lines on chart
input bool     ShowDebugInfo = true;        // Show debug info on chart

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+
CTrade         trade;
CPositionInfo  posInfo;
CSymbolInfo    symbolInfo;

// Pivot levels
double pivotPoint = 0;
double resistanceR1 = 0;
double resistanceR2 = 0;
double supportS1 = 0;
double supportS2 = 0;

// ATR
int atrHandle;
double atrBuffer[];

// Tracking
datetime lastPivotCalcTime = 0;
datetime lastEntryBarTime = 0;
double accountStartBalance = 0;
bool tradingEnabled = true;
bool breakoutTriggeredToday = false;

//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize trade object
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(Slippage);
    trade.SetTypeFilling(ORDER_FILLING_IOC);

    // Try different fill types if IOC fails
    if(!trade.SetTypeFilling(ORDER_FILLING_IOC))
        trade.SetTypeFilling(ORDER_FILLING_FOK);

    if(!symbolInfo.Name(_Symbol))
    {
        Print("Error initializing symbol info");
        return INIT_FAILED;
    }
    symbolInfo.Refresh();

    // Initialize ATR
    atrHandle = iATR(_Symbol, PERIOD_D1, 14);
    if(atrHandle == INVALID_HANDLE)
    {
        Print("Error creating ATR indicator");
        return INIT_FAILED;
    }
    ArraySetAsSeries(atrBuffer, true);

    accountStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);

    // Calculate initial pivots
    CalculateDailyPivots();

    if(ShowPivotLines)
        DrawPivotLines();

    Print("===========================================");
    Print("PivotBreakout EA v2.0 INITIALIZED");
    Print("Symbol: ", _Symbol);
    Print("Pivot: ", pivotPoint);
    Print("R1: ", resistanceR1);
    Print("R2: ", resistanceR2);
    Print("Entry level: ", UseR2Breakout ? resistanceR2 : resistanceR1);
    Print("Risk: ", RiskPercent, "% | R:R = ", RewardRiskRatio);
    Print("===========================================");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    ObjectDelete(0, "PivotLine");
    ObjectDelete(0, "R1Line");
    ObjectDelete(0, "R2Line");
    ObjectDelete(0, "S1Line");
    ObjectDelete(0, "S2Line");
    ObjectDelete(0, "DebugLabel");
    Comment("");

    if(atrHandle != INVALID_HANDLE)
        IndicatorRelease(atrHandle);

    Print("PivotBreakout EA deinitialized");
}

//+------------------------------------------------------------------+
void OnTick()
{
    // Check for new day - recalculate pivots
    datetime currentDay = iTime(_Symbol, PERIOD_D1, 0);
    if(currentDay != lastPivotCalcTime)
    {
        lastPivotCalcTime = currentDay;
        CalculateDailyPivots();
        breakoutTriggeredToday = false;  // Reset daily flag

        if(ShowPivotLines)
            DrawPivotLines();

        Print("New day - Pivots recalculated. R1=", resistanceR1, " Pivot=", pivotPoint);
    }

    // Update symbol info
    symbolInfo.Refresh();
    symbolInfo.RefreshRates();

    double currentBid = symbolInfo.Bid();
    double currentAsk = symbolInfo.Ask();
    double breakoutLevel = UseR2Breakout ? resistanceR2 : resistanceR1;

    // Show debug info
    if(ShowDebugInfo)
    {
        string info = StringFormat(
            "=== PivotBreakout EA v2 ===\n" +
            "Bid: %.5f | Ask: %.5f\n" +
            "Pivot: %.5f\n" +
            "R1: %.5f | R2: %.5f\n" +
            "S1: %.5f | S2: %.5f\n" +
            "Entry Level: %.5f\n" +
            "Distance to R1: %.1f pips\n" +
            "Positions: %d / %d\n" +
            "Breakout Today: %s\n" +
            "Trading Enabled: %s",
            currentBid, currentAsk,
            pivotPoint,
            resistanceR1, resistanceR2,
            supportS1, supportS2,
            breakoutLevel,
            (breakoutLevel - currentBid) / symbolInfo.Point() / 10,
            CountOpenPositions(), MaxOpenTrades,
            breakoutTriggeredToday ? "YES" : "NO",
            tradingEnabled ? "YES" : "NO"
        );
        Comment(info);
    }

    // Check drawdown
    CheckDrawdownLimit();
    if(!tradingEnabled) return;

    // Time filter
    if(UseTimeFilter && !IsWithinTradingHours()) return;

    // Manage existing positions
    ManageOpenPositions();

    // Check entry - use selected timeframe for entry
    ENUM_TIMEFRAMES entryTF = PERIOD_M15;
    if(EntryTimeframe == 5) entryTF = PERIOD_M5;
    else if(EntryTimeframe == 60) entryTF = PERIOD_H1;

    datetime currentBarTime = iTime(_Symbol, entryTF, 0);
    bool isNewBar = (currentBarTime != lastEntryBarTime);

    if(isNewBar)
    {
        lastEntryBarTime = currentBarTime;
        CheckEntrySignal(entryTF);
    }
}

//+------------------------------------------------------------------+
void CalculateDailyPivots()
{
    // Get PREVIOUS completed day's OHLC
    double prevHigh = iHigh(_Symbol, PERIOD_D1, 1);
    double prevLow = iLow(_Symbol, PERIOD_D1, 1);
    double prevClose = iClose(_Symbol, PERIOD_D1, 1);

    if(prevHigh == 0 || prevLow == 0 || prevClose == 0)
    {
        Print("Error: Could not get previous day data");
        return;
    }

    // Standard Pivot Point formula
    pivotPoint = (prevHigh + prevLow + prevClose) / 3.0;
    resistanceR1 = (2.0 * pivotPoint) - prevLow;
    resistanceR2 = pivotPoint + (prevHigh - prevLow);
    supportS1 = (2.0 * pivotPoint) - prevHigh;
    supportS2 = pivotPoint - (prevHigh - prevLow);

    // Normalize
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    pivotPoint = NormalizeDouble(pivotPoint, digits);
    resistanceR1 = NormalizeDouble(resistanceR1, digits);
    resistanceR2 = NormalizeDouble(resistanceR2, digits);
    supportS1 = NormalizeDouble(supportS1, digits);
    supportS2 = NormalizeDouble(supportS2, digits);
}

//+------------------------------------------------------------------+
void CheckEntrySignal(ENUM_TIMEFRAMES tf)
{
    // Skip if already have max positions
    if(CountOpenPositions() >= MaxOpenTrades)
        return;

    // Skip if already triggered today (optional - remove if you want multiple trades)
    if(breakoutTriggeredToday)
        return;

    double breakoutLevel = UseR2Breakout ? resistanceR2 : resistanceR1;
    double buffer = BreakoutBuffer * symbolInfo.Point();
    double entryTrigger = breakoutLevel + buffer;

    bool breakoutOccurred = false;

    if(RequireCloseAbove)
    {
        // Check if previous candle CLOSED above R1
        double prevClose = iClose(_Symbol, tf, 1);
        double prevPrevClose = iClose(_Symbol, tf, 2);

        breakoutOccurred = (prevClose > entryTrigger && prevPrevClose <= entryTrigger);
    }
    else
    {
        // Check if previous candle HIGH broke above R1 (more signals)
        double prevHigh = iHigh(_Symbol, tf, 1);
        double prevPrevHigh = iHigh(_Symbol, tf, 2);
        double currentPrice = symbolInfo.Ask();

        // Price broke above R1 and is still above
        breakoutOccurred = (prevHigh > entryTrigger && currentPrice > breakoutLevel);
    }

    if(breakoutOccurred)
    {
        Print(">>> BREAKOUT DETECTED! Price above ", breakoutLevel);
        ExecuteBuyOrder();
    }
}

//+------------------------------------------------------------------+
void ExecuteBuyOrder()
{
    symbolInfo.RefreshRates();

    double askPrice = symbolInfo.Ask();
    double stopLoss = pivotPoint;  // Stop at pivot
    double riskDistance = askPrice - stopLoss;

    if(riskDistance <= 0)
    {
        Print("Invalid risk distance (", riskDistance, "), skipping");
        return;
    }

    // Take profit
    double takeProfit = askPrice + (riskDistance * RewardRiskRatio);

    // Lot size
    double lotSize = CalculateLotSize(riskDistance);
    if(lotSize < symbolInfo.LotsMin())
    {
        Print("Lot size too small: ", lotSize, " < ", symbolInfo.LotsMin());
        lotSize = symbolInfo.LotsMin();
    }

    // Normalize
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    stopLoss = NormalizeDouble(stopLoss, digits);
    takeProfit = NormalizeDouble(takeProfit, digits);

    Print("Attempting BUY: Lots=", lotSize, " Ask=", askPrice, " SL=", stopLoss, " TP=", takeProfit);

    // Execute
    if(trade.Buy(lotSize, _Symbol, askPrice, stopLoss, takeProfit, "PivotBreakout"))
    {
        Print("*** BUY ORDER EXECUTED ***");
        Print("Ticket: ", trade.ResultOrder());
        breakoutTriggeredToday = true;
    }
    else
    {
        Print("BUY FAILED: Error ", trade.ResultRetcode(), " - ", trade.ResultRetcodeDescription());

        // Try without SL/TP first, then modify
        if(trade.Buy(lotSize, _Symbol, 0, 0, 0, "PivotBreakout"))
        {
            Print("Order placed without SL/TP, modifying...");
            ulong ticket = trade.ResultOrder();
            Sleep(100);
            trade.PositionModify(ticket, stopLoss, takeProfit);
            breakoutTriggeredToday = true;
        }
    }
}

//+------------------------------------------------------------------+
double CalculateLotSize(double riskDistance)
{
    if(FixedLotSize > 0)
        return NormalizeLotSize(FixedLotSize);

    double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double riskAmount = accountBalance * (RiskPercent / 100.0);
    double tickValue = symbolInfo.TickValue();
    double tickSize = symbolInfo.TickSize();

    if(tickSize == 0 || tickValue == 0)
        return symbolInfo.LotsMin();

    double riskInTicks = riskDistance / tickSize;
    double lotSize = riskAmount / (riskInTicks * tickValue);

    return NormalizeLotSize(lotSize);
}

//+------------------------------------------------------------------+
double NormalizeLotSize(double lots)
{
    double minLot = symbolInfo.LotsMin();
    double maxLot = symbolInfo.LotsMax();
    double lotStep = symbolInfo.LotsStep();

    lots = MathFloor(lots / lotStep) * lotStep;
    lots = MathMax(lots, minLot);
    lots = MathMin(lots, maxLot);

    return NormalizeDouble(lots, 2);
}

//+------------------------------------------------------------------+
void ManageOpenPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(!posInfo.SelectByIndex(i)) continue;
        if(posInfo.Magic() != MagicNumber) continue;
        if(posInfo.Symbol() != _Symbol) continue;

        double currentPrice = symbolInfo.Bid();

        // Exit if price drops below pivot
        if(currentPrice < pivotPoint)
        {
            Print("Price below pivot, closing position");
            ClosePosition(posInfo.Ticket());
            continue;
        }

        // Trailing stop
        if(TrailingStopEnabled)
            UpdateTrailingStop(posInfo.Ticket());
    }
}

//+------------------------------------------------------------------+
void UpdateTrailingStop(ulong ticket)
{
    if(!posInfo.SelectByTicket(ticket)) return;

    if(CopyBuffer(atrHandle, 0, 0, 1, atrBuffer) <= 0) return;

    double atr = atrBuffer[0];
    double trailDist = atr * TrailingStopATRMult;
    double currentPrice = symbolInfo.Bid();
    double currentSL = posInfo.StopLoss();
    double newSL = currentPrice - trailDist;

    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    newSL = NormalizeDouble(newSL, digits);

    // Only move up
    if(newSL > currentSL && newSL < currentPrice)
    {
        if(trade.PositionModify(ticket, newSL, posInfo.TakeProfit()))
            Print("Trailing stop updated to ", newSL);
    }
}

//+------------------------------------------------------------------+
void ClosePosition(ulong ticket)
{
    if(trade.PositionClose(ticket))
        Print("Position closed: ", ticket);
    else
        Print("Close failed: ", trade.ResultRetcode());
}

//+------------------------------------------------------------------+
int CountOpenPositions()
{
    int count = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(!posInfo.SelectByIndex(i)) continue;
        if(posInfo.Magic() == MagicNumber && posInfo.Symbol() == _Symbol)
            count++;
    }
    return count;
}

//+------------------------------------------------------------------+
void CheckDrawdownLimit()
{
    double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double dd = ((accountStartBalance - currentBalance) / accountStartBalance) * 100.0;

    if(dd >= MaxDrawdownPercent && tradingEnabled)
    {
        tradingEnabled = false;
        Print("MAX DRAWDOWN REACHED: ", dd, "%");
        CloseAllPositions();
    }
}

//+------------------------------------------------------------------+
void CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(!posInfo.SelectByIndex(i)) continue;
        if(posInfo.Magic() == MagicNumber && posInfo.Symbol() == _Symbol)
            trade.PositionClose(posInfo.Ticket());
    }
}

//+------------------------------------------------------------------+
bool IsWithinTradingHours()
{
    MqlDateTime t;
    TimeToStruct(TimeCurrent(), t);
    return (t.hour >= StartHour && t.hour < EndHour);
}

//+------------------------------------------------------------------+
void DrawPivotLines()
{
    DrawLine("PivotLine", pivotPoint, clrYellow, STYLE_SOLID, 2);
    DrawLine("R1Line", resistanceR1, clrLime, STYLE_DASH, 1);
    DrawLine("R2Line", resistanceR2, clrGreen, STYLE_DOT, 1);
    DrawLine("S1Line", supportS1, clrRed, STYLE_DASH, 1);
    DrawLine("S2Line", supportS2, clrMaroon, STYLE_DOT, 1);
}

//+------------------------------------------------------------------+
void DrawLine(string name, double price, color clr, ENUM_LINE_STYLE style, int width)
{
    if(ObjectFind(0, name) < 0)
        ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);

    ObjectSetDouble(0, name, OBJPROP_PRICE, price);
    ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
    ObjectSetInteger(0, name, OBJPROP_STYLE, style);
    ObjectSetInteger(0, name, OBJPROP_WIDTH, width);
    ObjectSetInteger(0, name, OBJPROP_BACK, true);
}

//+------------------------------------------------------------------+
void OnTrade() {}
void OnChartEvent(const int id, const long& lparam, const double& dparam, const string& sparam) {}
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                           PivotBreakout_EA.mq5   |
//|                                    Pivot Point Breakout Strategy |
//|                                                                  |
//| Strategy Rules:                                                  |
//| - BUY when price closes above R1 pivot resistance                |
//| - EXIT when price closes below pivot point                       |
//| - Stop Loss at pivot point level                                 |
//| - Take Profit at 2:1 or 3:1 risk/reward                         |
//+------------------------------------------------------------------+
#property copyright "Trading Backtest System"
#property link      ""
#property version   "1.00"
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
input double   FixedLotSize = 0.0;          // Fixed lot size (0 = use risk %)
input int      MaxOpenTrades = 1;           // Max simultaneous trades
input int      Slippage = 10;               // Maximum slippage (points)

input group "=== Pivot Settings ==="
input ENUM_TIMEFRAMES PivotTimeframe = PERIOD_D1;  // Timeframe for pivot calculation
input bool     UseR2Breakout = false;       // Use R2 instead of R1 for entry
input bool     TrailingStopEnabled = true;  // Enable trailing stop
input double   TrailingStopATRMult = 1.5;   // Trailing stop ATR multiplier

input group "=== Time Filter ==="
input bool     UseTimeFilter = false;       // Enable time filter
input int      StartHour = 9;               // Trading start hour
input int      EndHour = 17;                // Trading end hour

input group "=== Display ==="
input bool     ShowPivotLines = true;       // Show pivot lines on chart
input color    PivotColor = clrYellow;      // Pivot line color
input color    R1Color = clrLime;           // R1 line color
input color    R2Color = clrGreen;          // R2 line color
input color    S1Color = clrRed;            // S1 line color
input color    S2Color = clrMaroon;         // S2 line color

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

// ATR for position sizing
int atrHandle;
double atrBuffer[];

// Trade tracking
datetime lastBarTime = 0;
double accountStartBalance = 0;
bool tradingEnabled = true;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize trade object
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(Slippage);
    trade.SetTypeFilling(ORDER_FILLING_IOC);

    // Initialize symbol info
    if(!symbolInfo.Name(_Symbol))
    {
        Print("Error initializing symbol info");
        return INIT_FAILED;
    }

    // Initialize ATR indicator
    atrHandle = iATR(_Symbol, PivotTimeframe, 14);
    if(atrHandle == INVALID_HANDLE)
    {
        Print("Error creating ATR indicator");
        return INIT_FAILED;
    }
    ArraySetAsSeries(atrBuffer, true);

    // Store starting balance
    accountStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);

    // Calculate initial pivots
    CalculatePivotPoints();

    // Draw pivot lines
    if(ShowPivotLines)
        DrawPivotLines();

    Print("PivotBreakout EA initialized successfully");
    Print("Risk per trade: ", RiskPercent, "%");
    Print("Reward:Risk ratio: ", RewardRiskRatio, ":1");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Remove pivot lines
    ObjectDelete(0, "PivotLine");
    ObjectDelete(0, "R1Line");
    ObjectDelete(0, "R2Line");
    ObjectDelete(0, "S1Line");
    ObjectDelete(0, "S2Line");

    // Release indicator handle
    if(atrHandle != INVALID_HANDLE)
        IndicatorRelease(atrHandle);

    Print("PivotBreakout EA deinitialized");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if new bar formed
    datetime currentBarTime = iTime(_Symbol, PivotTimeframe, 0);
    bool isNewBar = (currentBarTime != lastBarTime);

    if(isNewBar)
    {
        lastBarTime = currentBarTime;

        // Recalculate pivots on new daily bar
        CalculatePivotPoints();

        // Update pivot lines
        if(ShowPivotLines)
            DrawPivotLines();
    }

    // Check drawdown limit
    CheckDrawdownLimit();

    if(!tradingEnabled)
        return;

    // Check time filter
    if(UseTimeFilter && !IsWithinTradingHours())
        return;

    // Update symbol info
    symbolInfo.Refresh();
    symbolInfo.RefreshRates();

    // Manage existing positions
    ManageOpenPositions();

    // Check for new entry signals (only on new bar to avoid multiple entries)
    if(isNewBar)
        CheckEntrySignal();
}

//+------------------------------------------------------------------+
//| Calculate Daily Pivot Points                                      |
//+------------------------------------------------------------------+
void CalculatePivotPoints()
{
    // Get previous day's OHLC
    double prevHigh = iHigh(_Symbol, PivotTimeframe, 1);
    double prevLow = iLow(_Symbol, PivotTimeframe, 1);
    double prevClose = iClose(_Symbol, PivotTimeframe, 1);

    // Standard Pivot Point formula
    pivotPoint = (prevHigh + prevLow + prevClose) / 3.0;

    // Resistance levels
    resistanceR1 = (2.0 * pivotPoint) - prevLow;
    resistanceR2 = pivotPoint + (prevHigh - prevLow);

    // Support levels
    supportS1 = (2.0 * pivotPoint) - prevHigh;
    supportS2 = pivotPoint - (prevHigh - prevLow);

    // Normalize to symbol digits
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    pivotPoint = NormalizeDouble(pivotPoint, digits);
    resistanceR1 = NormalizeDouble(resistanceR1, digits);
    resistanceR2 = NormalizeDouble(resistanceR2, digits);
    supportS1 = NormalizeDouble(supportS1, digits);
    supportS2 = NormalizeDouble(supportS2, digits);
}

//+------------------------------------------------------------------+
//| Check Entry Signal                                                |
//+------------------------------------------------------------------+
void CheckEntrySignal()
{
    // Skip if max trades reached
    if(CountOpenPositions() >= MaxOpenTrades)
        return;

    // Get current and previous close
    double currentClose = iClose(_Symbol, PivotTimeframe, 0);
    double previousClose = iClose(_Symbol, PivotTimeframe, 1);

    // Determine breakout level
    double breakoutLevel = UseR2Breakout ? resistanceR2 : resistanceR1;

    // BUY Signal: Price closes above R1 (or R2) and previous close was below
    if(currentClose > breakoutLevel && previousClose <= breakoutLevel)
    {
        ExecuteBuyOrder();
    }
}

//+------------------------------------------------------------------+
//| Execute Buy Order                                                 |
//+------------------------------------------------------------------+
void ExecuteBuyOrder()
{
    // Refresh rates
    symbolInfo.RefreshRates();

    double askPrice = symbolInfo.Ask();
    double stopLoss = pivotPoint;  // Stop at pivot point

    // Calculate risk distance
    double riskDistance = askPrice - stopLoss;

    if(riskDistance <= 0)
    {
        Print("Invalid risk distance, skipping trade");
        return;
    }

    // Calculate take profit based on R:R ratio
    double takeProfit = askPrice + (riskDistance * RewardRiskRatio);

    // Calculate lot size
    double lotSize = CalculateLotSize(riskDistance);

    if(lotSize < symbolInfo.LotsMin())
    {
        Print("Calculated lot size too small: ", lotSize);
        return;
    }

    // Normalize prices
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    stopLoss = NormalizeDouble(stopLoss, digits);
    takeProfit = NormalizeDouble(takeProfit, digits);

    // Execute trade
    if(trade.Buy(lotSize, _Symbol, askPrice, stopLoss, takeProfit, "PivotBreakout"))
    {
        Print("BUY order executed: Lots=", lotSize, " Entry=", askPrice,
              " SL=", stopLoss, " TP=", takeProfit);
    }
    else
    {
        Print("BUY order failed: ", trade.ResultRetcode(), " - ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Calculate Lot Size Based on Risk                                  |
//+------------------------------------------------------------------+
double CalculateLotSize(double riskDistance)
{
    // Use fixed lot size if specified
    if(FixedLotSize > 0)
        return NormalizeLotSize(FixedLotSize);

    // Calculate based on risk percentage
    double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double riskAmount = accountBalance * (RiskPercent / 100.0);

    // Get tick value
    double tickValue = symbolInfo.TickValue();
    double tickSize = symbolInfo.TickSize();

    if(tickSize == 0 || tickValue == 0)
        return symbolInfo.LotsMin();

    // Calculate lot size
    double riskInTicks = riskDistance / tickSize;
    double lotSize = riskAmount / (riskInTicks * tickValue);

    return NormalizeLotSize(lotSize);
}

//+------------------------------------------------------------------+
//| Normalize Lot Size to Broker Requirements                         |
//+------------------------------------------------------------------+
double NormalizeLotSize(double lots)
{
    double minLot = symbolInfo.LotsMin();
    double maxLot = symbolInfo.LotsMax();
    double lotStep = symbolInfo.LotsStep();

    // Round to lot step
    lots = MathFloor(lots / lotStep) * lotStep;

    // Ensure within limits
    lots = MathMax(lots, minLot);
    lots = MathMin(lots, maxLot);

    return NormalizeDouble(lots, 2);
}

//+------------------------------------------------------------------+
//| Manage Open Positions                                             |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(!posInfo.SelectByIndex(i))
            continue;

        // Only manage our positions
        if(posInfo.Magic() != MagicNumber)
            continue;

        if(posInfo.Symbol() != _Symbol)
            continue;

        // Check exit signal
        double currentClose = iClose(_Symbol, PERIOD_M1, 0);

        // EXIT Signal: Price closes below pivot point
        if(currentClose < pivotPoint)
        {
            ClosePosition(posInfo.Ticket());
            continue;
        }

        // Update trailing stop if enabled
        if(TrailingStopEnabled)
            UpdateTrailingStop(posInfo.Ticket());
    }
}

//+------------------------------------------------------------------+
//| Update Trailing Stop                                              |
//+------------------------------------------------------------------+
void UpdateTrailingStop(ulong ticket)
{
    if(!posInfo.SelectByTicket(ticket))
        return;

    // Get ATR value
    if(CopyBuffer(atrHandle, 0, 0, 1, atrBuffer) <= 0)
        return;

    double atr = atrBuffer[0];
    double trailingDistance = atr * TrailingStopATRMult;

    double currentPrice = symbolInfo.Bid();
    double currentSL = posInfo.StopLoss();
    double newSL = currentPrice - trailingDistance;

    // Normalize
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    newSL = NormalizeDouble(newSL, digits);

    // Only move stop loss up, never down
    if(newSL > currentSL && newSL < currentPrice)
    {
        trade.PositionModify(ticket, newSL, posInfo.TakeProfit());
    }
}

//+------------------------------------------------------------------+
//| Close Position                                                    |
//+------------------------------------------------------------------+
void ClosePosition(ulong ticket)
{
    if(trade.PositionClose(ticket))
    {
        Print("Position closed: Ticket=", ticket);
    }
    else
    {
        Print("Failed to close position: ", trade.ResultRetcode());
    }
}

//+------------------------------------------------------------------+
//| Count Open Positions                                              |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
    int count = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(!posInfo.SelectByIndex(i))
            continue;

        if(posInfo.Magic() == MagicNumber && posInfo.Symbol() == _Symbol)
            count++;
    }

    return count;
}

//+------------------------------------------------------------------+
//| Check Drawdown Limit                                              |
//+------------------------------------------------------------------+
void CheckDrawdownLimit()
{
    double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double drawdownPercent = ((accountStartBalance - currentBalance) / accountStartBalance) * 100.0;

    if(drawdownPercent >= MaxDrawdownPercent)
    {
        if(tradingEnabled)
        {
            tradingEnabled = false;
            Print("TRADING DISABLED: Max drawdown reached (", drawdownPercent, "%)");

            // Close all positions
            CloseAllPositions();
        }
    }
}

//+------------------------------------------------------------------+
//| Close All Positions                                               |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(!posInfo.SelectByIndex(i))
            continue;

        if(posInfo.Magic() == MagicNumber && posInfo.Symbol() == _Symbol)
        {
            trade.PositionClose(posInfo.Ticket());
        }
    }
}

//+------------------------------------------------------------------+
//| Check if Within Trading Hours                                     |
//+------------------------------------------------------------------+
bool IsWithinTradingHours()
{
    MqlDateTime timeStruct;
    TimeToStruct(TimeCurrent(), timeStruct);

    int currentHour = timeStruct.hour;

    return (currentHour >= StartHour && currentHour < EndHour);
}

//+------------------------------------------------------------------+
//| Draw Pivot Lines on Chart                                         |
//+------------------------------------------------------------------+
void DrawPivotLines()
{
    datetime startTime = iTime(_Symbol, PivotTimeframe, 1);
    datetime endTime = iTime(_Symbol, PivotTimeframe, 0) + PeriodSeconds(PivotTimeframe);

    DrawHorizontalLine("PivotLine", pivotPoint, PivotColor, STYLE_SOLID, 2, "PP");
    DrawHorizontalLine("R1Line", resistanceR1, R1Color, STYLE_DASH, 1, "R1");
    DrawHorizontalLine("R2Line", resistanceR2, R2Color, STYLE_DASH, 1, "R2");
    DrawHorizontalLine("S1Line", supportS1, S1Color, STYLE_DASH, 1, "S1");
    DrawHorizontalLine("S2Line", supportS2, S2Color, STYLE_DASH, 1, "S2");
}

//+------------------------------------------------------------------+
//| Draw Horizontal Line                                              |
//+------------------------------------------------------------------+
void DrawHorizontalLine(string name, double price, color lineColor,
                        ENUM_LINE_STYLE style, int width, string label)
{
    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);
    }
    else
    {
        ObjectSetDouble(0, name, OBJPROP_PRICE, price);
    }

    ObjectSetInteger(0, name, OBJPROP_COLOR, lineColor);
    ObjectSetInteger(0, name, OBJPROP_STYLE, style);
    ObjectSetInteger(0, name, OBJPROP_WIDTH, width);
    ObjectSetString(0, name, OBJPROP_TEXT, label + ": " + DoubleToString(price, _Digits));
    ObjectSetInteger(0, name, OBJPROP_BACK, true);
    ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| OnTrade Event Handler                                             |
//+------------------------------------------------------------------+
void OnTrade()
{
    // Log trade events
    static int lastDealsCount = 0;
    int currentDealsCount = HistoryDealsTotal();

    if(currentDealsCount > lastDealsCount)
    {
        // New deal executed
        lastDealsCount = currentDealsCount;
    }
}

//+------------------------------------------------------------------+
//| ChartEvent Handler                                                |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long& lparam, const double& dparam, const string& sparam)
{
    // Handle chart events if needed
}
//+------------------------------------------------------------------+

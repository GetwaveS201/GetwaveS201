"""
Risk Manager Module for Stock Trading Backtest System
Handles position sizing, stop losses, and portfolio-level risk constraints.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from indicators import TechnicalIndicators as ti


class RiskLevel(Enum):
    """Risk level classifications."""
    LOW = 1
    MODERATE = 2
    HIGH = 3
    EXTREME = 4


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    entry_date: datetime
    entry_price: float
    shares: int
    direction: str = 'long'
    stop_loss: float = 0.0
    take_profit: float = 0.0
    sector: str = 'Unknown'
    risk_amount: float = 0.0


@dataclass
class RiskConfig:
    """Risk management configuration."""
    # Position-level risk
    max_risk_per_trade_pct: float = 2.0  # Max 2% risk per trade
    max_position_size_pct: float = 20.0  # Max 20% of portfolio in one position
    default_stop_atr_mult: float = 1.5  # Default stop = 1.5x ATR
    max_stop_pct: float = 6.0  # Max 6% stop loss

    # Portfolio-level risk
    max_positions: int = 5  # Max concurrent positions
    max_portfolio_heat_pct: float = 10.0  # Max total risk exposure
    max_sector_concentration_pct: float = 40.0  # Max 40% in one sector
    max_correlated_positions: int = 3  # Max positions with correlation >0.7

    # Take profit settings
    min_reward_risk_ratio: float = 2.0  # Minimum 2:1 reward/risk
    default_reward_risk_ratio: float = 3.0  # Default 3:1 target

    # Trailing stop settings
    use_trailing_stops: bool = True
    trailing_stop_activation_pct: float = 5.0  # Activate after 5% profit
    trailing_stop_distance_pct: float = 3.0  # Trail by 3%


class RiskManager:
    """
    Comprehensive risk management system for trading.
    """

    # Sector classifications for common stocks
    SECTOR_MAP = {
        # Technology
        'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'GOOG': 'Technology',
        'NVDA': 'Technology', 'META': 'Technology', 'ADBE': 'Technology', 'CRM': 'Technology',
        'CSCO': 'Technology', 'INTC': 'Technology', 'AMD': 'Technology', 'TXN': 'Technology',
        'QCOM': 'Technology', 'IBM': 'Technology', 'AVGO': 'Technology', 'ORCL': 'Technology',

        # Consumer Discretionary
        'AMZN': 'Consumer', 'TSLA': 'Consumer', 'HD': 'Consumer', 'NKE': 'Consumer',
        'MCD': 'Consumer', 'SBUX': 'Consumer', 'LOW': 'Consumer', 'TJX': 'Consumer',
        'BKNG': 'Consumer',

        # Healthcare
        'UNH': 'Healthcare', 'JNJ': 'Healthcare', 'MRK': 'Healthcare', 'ABBV': 'Healthcare',
        'LLY': 'Healthcare', 'PFE': 'Healthcare', 'TMO': 'Healthcare', 'ABT': 'Healthcare',
        'DHR': 'Healthcare', 'BMY': 'Healthcare', 'ISRG': 'Healthcare', 'GILD': 'Healthcare',
        'CVS': 'Healthcare', 'REGN': 'Healthcare', 'SYK': 'Healthcare', 'VRTX': 'Healthcare',
        'ZTS': 'Healthcare', 'CI': 'Healthcare', 'BDX': 'Healthcare', 'BSX': 'Healthcare',

        # Financials
        'BRK-B': 'Financials', 'JPM': 'Financials', 'V': 'Financials', 'MA': 'Financials',
        'BAC': 'Financials', 'GS': 'Financials', 'MS': 'Financials', 'BLK': 'Financials',
        'SPGI': 'Financials', 'MMC': 'Financials', 'C': 'Financials', 'SCHW': 'Financials',
        'PNC': 'Financials', 'USB': 'Financials', 'AON': 'Financials', 'ICE': 'Financials',
        'CME': 'Financials', 'CB': 'Financials',

        # Energy
        'XOM': 'Energy', 'CVX': 'Energy', 'SLB': 'Energy', 'EOG': 'Energy',

        # Consumer Staples
        'PG': 'Consumer Staples', 'PEP': 'Consumer Staples', 'KO': 'Consumer Staples',
        'COST': 'Consumer Staples', 'WMT': 'Consumer Staples', 'PM': 'Consumer Staples',
        'MDLZ': 'Consumer Staples', 'MO': 'Consumer Staples', 'CL': 'Consumer Staples',

        # Industrials
        'HON': 'Industrials', 'UPS': 'Industrials', 'RTX': 'Industrials', 'CAT': 'Industrials',
        'BA': 'Industrials', 'DE': 'Industrials', 'GE': 'Industrials', 'MMM': 'Industrials',
        'ITW': 'Industrials', 'EMR': 'Industrials', 'NOC': 'Industrials', 'GD': 'Industrials',
        'WM': 'Industrials',

        # Utilities
        'NEE': 'Utilities', 'DUK': 'Utilities', 'SO': 'Utilities',

        # Real Estate
        'PLD': 'Real Estate', 'AMT': 'Real Estate', 'EQIX': 'Real Estate',

        # Communication Services
        'VZ': 'Communication', 'T': 'Communication', 'CMCSA': 'Communication',

        # Materials
        'APD': 'Materials', 'LIN': 'Materials',

        # ETFs
        'SPY': 'ETF', 'QQQ': 'ETF', 'IWM': 'ETF',
    }

    def __init__(self, config: RiskConfig = None, initial_capital: float = 100_000):
        """
        Initialize Risk Manager.

        Args:
            config: RiskConfig object
            initial_capital: Starting capital
        """
        self.config = config or RiskConfig()
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.open_positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []

    def get_sector(self, symbol: str) -> str:
        """Get sector for a symbol."""
        return self.SECTOR_MAP.get(symbol, 'Unknown')

    def calculate_position_size(self, symbol: str, entry_price: float,
                                stop_loss: float, current_capital: float = None) -> Tuple[int, float, str]:
        """
        Calculate position size based on risk parameters.

        Args:
            symbol: Stock symbol
            entry_price: Planned entry price
            stop_loss: Stop loss price
            current_capital: Current portfolio value (uses stored value if not provided)

        Returns:
            Tuple of (shares, position_value, rejection_reason or '')
        """
        capital = current_capital or self.current_capital

        # Validate inputs
        if entry_price <= 0 or stop_loss <= 0:
            return 0, 0, "Invalid prices"

        if stop_loss >= entry_price:
            return 0, 0, "Stop loss must be below entry for long positions"

        # Calculate risk per share
        risk_per_share = entry_price - stop_loss
        risk_pct = risk_per_share / entry_price * 100

        # Check max stop loss
        if risk_pct > self.config.max_stop_pct:
            return 0, 0, f"Stop too wide: {risk_pct:.1f}% > {self.config.max_stop_pct}%"

        # Calculate max risk amount
        max_risk_amount = capital * (self.config.max_risk_per_trade_pct / 100)

        # Calculate shares based on risk
        shares = int(max_risk_amount / risk_per_share)

        # Check max position size
        position_value = shares * entry_price
        max_position_value = capital * (self.config.max_position_size_pct / 100)

        if position_value > max_position_value:
            shares = int(max_position_value / entry_price)
            position_value = shares * entry_price

        # Ensure at least 1 share
        if shares < 1:
            return 0, 0, "Position too small"

        return shares, position_value, ""

    def calculate_stop_loss(self, df: pd.DataFrame, entry_idx: int,
                            entry_price: float, method: str = 'atr') -> float:
        """
        Calculate stop loss price using various methods.

        Args:
            df: Price DataFrame
            entry_idx: Index of entry bar
            entry_price: Entry price
            method: 'atr', 'swing', 'percent', or 'support'

        Returns:
            Stop loss price
        """
        if method == 'atr':
            atr = ti.atr(df, 14)
            stop = entry_price - (self.config.default_stop_atr_mult * atr.iloc[entry_idx])

        elif method == 'swing':
            # Use recent swing low
            lookback = min(20, entry_idx)
            recent_low = df['low'].iloc[entry_idx-lookback:entry_idx+1].min()
            atr = ti.atr(df, 14)
            stop = recent_low - (0.5 * atr.iloc[entry_idx])

        elif method == 'percent':
            stop = entry_price * (1 - self.config.max_stop_pct / 100)

        elif method == 'support':
            # Use Bollinger lower band or recent support
            _, _, lower = ti.bollinger_bands(df['close'], 20, 2.0)
            stop = lower.iloc[entry_idx]

        else:
            stop = entry_price * (1 - self.config.max_stop_pct / 100)

        # Ensure stop is not too far
        max_stop_distance = entry_price * (self.config.max_stop_pct / 100)
        min_stop = entry_price - max_stop_distance
        stop = max(stop, min_stop)

        return stop

    def calculate_take_profit(self, entry_price: float, stop_loss: float,
                              reward_risk: float = None) -> float:
        """
        Calculate take profit price based on reward/risk ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            reward_risk: Reward to risk ratio (uses default if not provided)

        Returns:
            Take profit price
        """
        rr = reward_risk or self.config.default_reward_risk_ratio
        risk = entry_price - stop_loss
        return entry_price + (rr * risk)

    def can_open_position(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if a new position can be opened.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (can_open, reason if not)
        """
        # Check max positions
        if len(self.open_positions) >= self.config.max_positions:
            return False, f"Max positions reached: {self.config.max_positions}"

        # Check if already in position
        if symbol in self.open_positions:
            return False, f"Already in position: {symbol}"

        # Check sector concentration
        sector = self.get_sector(symbol)
        sector_exposure = self._calculate_sector_exposure()

        if sector in sector_exposure:
            current_pct = sector_exposure[sector] / self.current_capital * 100
            if current_pct >= self.config.max_sector_concentration_pct:
                return False, f"Sector {sector} at max: {current_pct:.1f}%"

        # Check portfolio heat
        total_risk = self._calculate_portfolio_heat()
        if total_risk >= self.config.max_portfolio_heat_pct:
            return False, f"Portfolio heat at max: {total_risk:.1f}%"

        return True, ""

    def _calculate_sector_exposure(self) -> Dict[str, float]:
        """Calculate current exposure by sector."""
        exposure = {}
        for symbol, pos in self.open_positions.items():
            sector = pos.sector
            value = pos.shares * pos.entry_price
            exposure[sector] = exposure.get(sector, 0) + value
        return exposure

    def _calculate_portfolio_heat(self) -> float:
        """Calculate total portfolio risk (heat)."""
        total_risk = 0
        for pos in self.open_positions.values():
            total_risk += pos.risk_amount
        return (total_risk / self.current_capital) * 100

    def add_position(self, symbol: str, entry_date: datetime, entry_price: float,
                     shares: int, stop_loss: float, take_profit: float) -> bool:
        """
        Add a new position to tracking.

        Args:
            symbol: Stock symbol
            entry_date: Entry datetime
            entry_price: Entry price
            shares: Number of shares
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            True if position added successfully
        """
        can_open, reason = self.can_open_position(symbol)
        if not can_open:
            return False

        risk_amount = (entry_price - stop_loss) * shares

        self.open_positions[symbol] = Position(
            symbol=symbol,
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
            sector=self.get_sector(symbol),
            risk_amount=risk_amount
        )

        return True

    def close_position(self, symbol: str, exit_price: float, exit_date: datetime,
                       exit_reason: str) -> Optional[Dict]:
        """
        Close an open position.

        Args:
            symbol: Stock symbol
            exit_price: Exit price
            exit_date: Exit datetime
            exit_reason: Reason for exit

        Returns:
            Trade record dictionary or None if not found
        """
        if symbol not in self.open_positions:
            return None

        pos = self.open_positions[symbol]

        pnl = (exit_price - pos.entry_price) * pos.shares
        pnl_pct = (exit_price / pos.entry_price - 1) * 100

        trade = {
            'symbol': symbol,
            'sector': pos.sector,
            'entry_date': pos.entry_date,
            'entry_price': pos.entry_price,
            'exit_date': exit_date,
            'exit_price': exit_price,
            'shares': pos.shares,
            'stop_loss': pos.stop_loss,
            'take_profit': pos.take_profit,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': exit_reason
        }

        self.trade_history.append(trade)
        self.current_capital += pnl

        del self.open_positions[symbol]

        return trade

    def update_trailing_stop(self, symbol: str, current_price: float) -> Optional[float]:
        """
        Update trailing stop for a position.

        Args:
            symbol: Stock symbol
            current_price: Current market price

        Returns:
            New stop loss price or None if not updated
        """
        if symbol not in self.open_positions:
            return None

        pos = self.open_positions[symbol]

        # Check if trailing stop should be activated
        profit_pct = (current_price - pos.entry_price) / pos.entry_price * 100

        if profit_pct < self.config.trailing_stop_activation_pct:
            return None

        # Calculate new trailing stop
        new_stop = current_price * (1 - self.config.trailing_stop_distance_pct / 100)

        # Only update if new stop is higher
        if new_stop > pos.stop_loss:
            pos.stop_loss = new_stop
            return new_stop

        return None

    def assess_market_risk(self, vix: float, spy_trend: bool) -> RiskLevel:
        """
        Assess overall market risk level.

        Args:
            vix: Current VIX value
            spy_trend: True if SPY in uptrend

        Returns:
            RiskLevel enum value
        """
        if vix > 30:
            return RiskLevel.EXTREME
        elif vix > 25 and not spy_trend:
            return RiskLevel.HIGH
        elif vix > 20 or not spy_trend:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW

    def adjust_for_market_risk(self, risk_level: RiskLevel) -> Dict[str, float]:
        """
        Adjust risk parameters based on market conditions.

        Args:
            risk_level: Current market risk level

        Returns:
            Dictionary of adjusted parameters
        """
        adjustments = {
            'max_positions': self.config.max_positions,
            'max_risk_per_trade': self.config.max_risk_per_trade_pct,
            'position_size_mult': 1.0
        }

        if risk_level == RiskLevel.EXTREME:
            adjustments['max_positions'] = 2
            adjustments['max_risk_per_trade'] = 1.0
            adjustments['position_size_mult'] = 0.5
        elif risk_level == RiskLevel.HIGH:
            adjustments['max_positions'] = 3
            adjustments['max_risk_per_trade'] = 1.5
            adjustments['position_size_mult'] = 0.75
        elif risk_level == RiskLevel.MODERATE:
            adjustments['max_positions'] = 4
            adjustments['max_risk_per_trade'] = 2.0
            adjustments['position_size_mult'] = 0.9

        return adjustments

    def get_portfolio_summary(self) -> Dict:
        """Get summary of current portfolio state."""
        total_value = sum(pos.shares * pos.entry_price for pos in self.open_positions.values())
        total_risk = sum(pos.risk_amount for pos in self.open_positions.values())
        sector_exposure = self._calculate_sector_exposure()

        return {
            'cash': self.current_capital - total_value,
            'positions_value': total_value,
            'total_value': self.current_capital,
            'num_positions': len(self.open_positions),
            'total_risk_pct': (total_risk / self.current_capital) * 100,
            'sector_exposure': sector_exposure,
            'positions': list(self.open_positions.keys())
        }

    def generate_risk_report(self) -> str:
        """Generate a risk report string."""
        summary = self.get_portfolio_summary()

        report = []
        report.append("=" * 50)
        report.append("PORTFOLIO RISK REPORT")
        report.append("=" * 50)
        report.append(f"Total Capital:    ${summary['total_value']:,.2f}")
        report.append(f"Cash:             ${summary['cash']:,.2f}")
        report.append(f"Positions Value:  ${summary['positions_value']:,.2f}")
        report.append(f"Open Positions:   {summary['num_positions']}/{self.config.max_positions}")
        report.append(f"Portfolio Heat:   {summary['total_risk_pct']:.1f}% / {self.config.max_portfolio_heat_pct}%")

        report.append("\nSector Exposure:")
        for sector, value in summary['sector_exposure'].items():
            pct = value / self.current_capital * 100
            report.append(f"  {sector:15} ${value:>10,.2f} ({pct:5.1f}%)")

        if self.open_positions:
            report.append("\nOpen Positions:")
            for symbol, pos in self.open_positions.items():
                report.append(f"  {symbol:6} {pos.shares:>5} shares @ ${pos.entry_price:.2f}")
                report.append(f"         Stop: ${pos.stop_loss:.2f}  Target: ${pos.take_profit:.2f}")

        return "\n".join(report)


def calculate_correlation_matrix(stock_data: Dict[str, pd.DataFrame],
                                 symbols: List[str],
                                 lookback: int = 60) -> pd.DataFrame:
    """
    Calculate correlation matrix for given symbols.

    Args:
        stock_data: Dictionary of price DataFrames
        symbols: List of symbols to include
        lookback: Number of days for correlation calculation

    Returns:
        Correlation matrix DataFrame
    """
    returns = {}

    for symbol in symbols:
        if symbol in stock_data:
            df = stock_data[symbol]
            if len(df) >= lookback:
                ret = df['close'].pct_change().iloc[-lookback:]
                returns[symbol] = ret

    if not returns:
        return pd.DataFrame()

    returns_df = pd.DataFrame(returns)
    return returns_df.corr()


def find_uncorrelated_positions(stock_data: Dict[str, pd.DataFrame],
                                candidates: List[str],
                                existing: List[str],
                                max_correlation: float = 0.7) -> List[str]:
    """
    Find candidates that are not highly correlated with existing positions.

    Args:
        stock_data: Dictionary of price DataFrames
        candidates: List of candidate symbols
        existing: List of existing position symbols
        max_correlation: Maximum allowed correlation

    Returns:
        List of uncorrelated candidates
    """
    if not existing:
        return candidates

    all_symbols = list(set(candidates + existing))
    corr_matrix = calculate_correlation_matrix(stock_data, all_symbols)

    if corr_matrix.empty:
        return candidates

    uncorrelated = []
    for candidate in candidates:
        if candidate not in corr_matrix.columns:
            uncorrelated.append(candidate)
            continue

        is_correlated = False
        for exist in existing:
            if exist in corr_matrix.columns:
                corr = abs(corr_matrix.loc[candidate, exist])
                if corr > max_correlation:
                    is_correlated = True
                    break

        if not is_correlated:
            uncorrelated.append(candidate)

    return uncorrelated


if __name__ == '__main__':
    # Test risk manager
    print("Testing Risk Manager...")
    print("-" * 50)

    config = RiskConfig(
        max_risk_per_trade_pct=2.0,
        max_position_size_pct=20.0,
        max_positions=5,
        max_portfolio_heat_pct=10.0
    )

    rm = RiskManager(config, initial_capital=100_000)

    # Test position sizing
    print("\n1. Position Sizing Test:")
    entry_price = 150.0
    stop_loss = 145.0  # $5 risk per share

    shares, value, reason = rm.calculate_position_size('AAPL', entry_price, stop_loss)
    print(f"   Entry: ${entry_price}, Stop: ${stop_loss}")
    print(f"   Shares: {shares}, Value: ${value:,.2f}")
    print(f"   Risk per share: ${entry_price - stop_loss}")
    print(f"   Total risk: ${(entry_price - stop_loss) * shares:,.2f}")

    # Test adding positions
    print("\n2. Position Management Test:")
    from datetime import datetime

    can_open, reason = rm.can_open_position('AAPL')
    print(f"   Can open AAPL: {can_open}")

    rm.add_position('AAPL', datetime.now(), 150.0, 100, 145.0, 165.0)
    rm.add_position('MSFT', datetime.now(), 400.0, 50, 380.0, 450.0)
    rm.add_position('GOOGL', datetime.now(), 140.0, 70, 135.0, 155.0)

    print(f"\n   Positions: {list(rm.open_positions.keys())}")

    # Test risk report
    print("\n3. Risk Report:")
    print(rm.generate_risk_report())

    # Test market risk assessment
    print("\n4. Market Risk Assessment:")
    for vix, trend in [(15, True), (22, True), (28, False), (35, False)]:
        level = rm.assess_market_risk(vix, trend)
        adjustments = rm.adjust_for_market_risk(level)
        print(f"   VIX: {vix}, Uptrend: {trend} -> {level.name}")
        print(f"      Max positions: {adjustments['max_positions']}, "
              f"Size mult: {adjustments['position_size_mult']}")

    # Test closing position
    print("\n5. Close Position Test:")
    trade = rm.close_position('AAPL', 160.0, datetime.now(), 'Take Profit')
    if trade:
        print(f"   Closed AAPL: P&L ${trade['pnl']:,.2f} ({trade['pnl_pct']:.1f}%)")
        print(f"   Exit reason: {trade['exit_reason']}")

    print("\n" + rm.generate_risk_report())

    print("\nRisk Manager test completed!")

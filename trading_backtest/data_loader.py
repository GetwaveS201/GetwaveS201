"""
Data Loader Module for Stock Trading Backtest System
Downloads and cleans stock data from yfinance with survivorship bias handling.
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')


# Top 100 liquid stocks from Russell 1000 (selected for liquidity and coverage)
TOP_100_STOCKS = [
    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH',
    'JNJ', 'XOM', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV',
    'LLY', 'PEP', 'KO', 'COST', 'AVGO', 'WMT', 'MCD', 'CSCO', 'TMO', 'ACN',
    'ABT', 'DHR', 'NEE', 'VZ', 'ADBE', 'CRM', 'NKE', 'PM', 'TXN', 'QCOM',
    'CMCSA', 'RTX', 'UPS', 'HON', 'INTC', 'IBM', 'AMD', 'LOW', 'SPGI', 'CAT',
    'BA', 'GS', 'DE', 'BMY', 'ISRG', 'SBUX', 'BLK', 'INTU', 'PLD', 'GILD',
    'MDLZ', 'ADP', 'AMT', 'CVS', 'ADI', 'REGN', 'SYK', 'BKNG', 'MMC', 'VRTX',
    'T', 'C', 'MS', 'ZTS', 'CI', 'TJX', 'SO', 'MO', 'BDX', 'SCHW',
    'DUK', 'CL', 'ITW', 'EOG', 'CB', 'PNC', 'SLB', 'LRCX', 'BSX', 'MMM',
    'USB', 'APD', 'AON', 'ICE', 'CME', 'EQIX', 'NOC', 'WM', 'EMR', 'GD'
]

# Core ETFs for market analysis
CORE_ETFS = ['SPY', 'QQQ', 'IWM']

# Volatility index
VOLATILITY_INDEX = ['^VIX']


class DataLoader:
    """
    Handles downloading, cleaning, and storing stock data for backtesting.
    """

    def __init__(self,
                 data_dir: str = 'data',
                 start_date: str = '2015-01-01',
                 end_date: str = '2025-01-01',
                 min_price: float = 5.0,
                 min_volume: float = 50_000_000):
        """
        Initialize DataLoader.

        Args:
            data_dir: Directory to store cached data
            start_date: Start date for historical data
            end_date: End date for historical data
            min_price: Minimum price filter (default $5)
            min_volume: Minimum daily dollar volume filter (default $50M)
        """
        self.data_dir = data_dir
        self.start_date = start_date
        self.end_date = end_date
        self.min_price = min_price
        self.min_volume = min_volume

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Storage for data
        self.stock_data: Dict[str, pd.DataFrame] = {}
        self.vix_data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, dict] = {}

    def download_single_stock(self, symbol: str, retries: int = 3) -> Optional[pd.DataFrame]:
        """
        Download data for a single stock with retry logic.

        Args:
            symbol: Stock ticker symbol
            retries: Number of retry attempts

        Returns:
            DataFrame with OHLCV data or None if download fails
        """
        for attempt in range(retries):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=self.start_date,
                    end=self.end_date,
                    auto_adjust=False
                )

                if df.empty:
                    return None

                # Standardize column names
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]

                # Ensure we have the required columns
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                if not all(col in df.columns for col in required_cols):
                    return None

                # Calculate adjusted close if not present
                if 'adj_close' not in df.columns and 'adj close' not in df.columns:
                    if 'dividends' in df.columns and 'stock_splits' in df.columns:
                        df['adj_close'] = df['close']  # Simplified - yfinance handles adjustments
                    else:
                        df['adj_close'] = df['close']

                # Rename adj close column if needed
                if 'adj close' in df.columns:
                    df.rename(columns={'adj close': 'adj_close'}, inplace=True)

                # Keep only essential columns
                keep_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
                df = df[[c for c in keep_cols if c in df.columns]]

                # Remove timezone from index
                df.index = df.index.tz_localize(None)

                return df

            except Exception as e:
                if attempt < retries - 1:
                    continue
                print(f"Failed to download {symbol}: {str(e)}")
                return None

        return None

    def validate_data_quality(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, str]:
        """
        Validate data quality for a stock.

        Args:
            df: Stock price DataFrame
            symbol: Ticker symbol

        Returns:
            Tuple of (is_valid, reason)
        """
        if df is None or df.empty:
            return False, "Empty data"

        # Check for minimum data points (at least 2 years of trading days)
        if len(df) < 500:
            return False, f"Insufficient data points: {len(df)}"

        # Check for minimum price
        avg_price = df['close'].mean()
        if avg_price < self.min_price:
            return False, f"Average price too low: ${avg_price:.2f}"

        # Check for minimum volume
        avg_dollar_volume = (df['close'] * df['volume']).mean()
        if avg_dollar_volume < self.min_volume:
            return False, f"Average dollar volume too low: ${avg_dollar_volume/1e6:.1f}M"

        # Check for suspicious data (extreme moves)
        daily_returns = df['close'].pct_change()
        extreme_moves = (daily_returns.abs() > 0.5).sum()
        if extreme_moves > 10:
            return False, f"Too many extreme moves (>50%): {extreme_moves}"

        # Check for missing data (gaps > 5 trading days)
        date_diffs = pd.Series(df.index).diff()
        max_gap = date_diffs.max()
        if max_gap and max_gap > timedelta(days=10):
            return False, f"Data gap too large: {max_gap.days} days"

        # Check for data quality issues
        null_count = df.isnull().sum().sum()
        null_pct = null_count / (len(df) * len(df.columns))
        if null_pct > 0.05:
            return False, f"Too many null values: {null_pct:.1%}"

        return True, "Valid"

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize stock data.

        Args:
            df: Raw stock DataFrame

        Returns:
            Cleaned DataFrame
        """
        if df is None or df.empty:
            return df

        # Make a copy
        df = df.copy()

        # Forward fill missing values (for holidays, etc.)
        df = df.ffill()

        # Backward fill any remaining NaN at the start
        df = df.bfill()

        # Remove duplicate indices
        df = df[~df.index.duplicated(keep='first')]

        # Sort by date
        df = df.sort_index()

        # Handle zero volumes by forward filling
        df['volume'] = df['volume'].replace(0, np.nan).ffill()

        # Ensure no negative values
        for col in ['open', 'high', 'low', 'close', 'adj_close', 'volume']:
            if col in df.columns:
                df[col] = df[col].clip(lower=0.001)

        # Ensure OHLC relationships
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)

        return df

    def handle_splits_dividends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adjust for stock splits and dividends.
        Note: yfinance typically handles this, but we add extra validation.

        Args:
            df: Stock DataFrame

        Returns:
            Adjusted DataFrame
        """
        if df is None or df.empty:
            return df

        df = df.copy()

        # Calculate adjustment factor from close to adj_close
        if 'adj_close' in df.columns:
            adj_factor = df['adj_close'] / df['close']

            # Apply adjustment to all price columns
            for col in ['open', 'high', 'low']:
                if col in df.columns:
                    df[f'{col}_adjusted'] = df[col] * adj_factor

        return df

    def download_all_stocks(self, include_etfs: bool = True,
                           include_vix: bool = True,
                           verbose: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Download data for all stocks in the universe.

        Args:
            include_etfs: Include ETFs (SPY, QQQ, IWM)
            include_vix: Include VIX data
            verbose: Print progress

        Returns:
            Dictionary of DataFrames by symbol
        """
        # Build symbol list
        symbols = list(TOP_100_STOCKS)
        if include_etfs:
            symbols = CORE_ETFS + symbols

        total = len(symbols)
        successful = 0
        failed = []

        if verbose:
            print(f"Downloading data for {total} symbols...")
            print(f"Date range: {self.start_date} to {self.end_date}")
            print("-" * 50)

        for i, symbol in enumerate(symbols):
            if verbose and (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{total} ({successful} successful)")

            # Download data
            df = self.download_single_stock(symbol)

            # Validate
            is_valid, reason = self.validate_data_quality(df, symbol)

            if is_valid:
                # Clean and store
                df = self.clean_data(df)
                df = self.handle_splits_dividends(df)
                self.stock_data[symbol] = df
                self.metadata[symbol] = {
                    'start_date': df.index.min(),
                    'end_date': df.index.max(),
                    'data_points': len(df),
                    'avg_price': df['close'].mean(),
                    'avg_volume': df['volume'].mean()
                }
                successful += 1
            else:
                failed.append((symbol, reason))

        # Download VIX data
        if include_vix:
            if verbose:
                print("\nDownloading VIX data...")
            vix_df = self.download_single_stock('^VIX')
            if vix_df is not None:
                self.vix_data = self.clean_data(vix_df)
                if verbose:
                    print("VIX data downloaded successfully")
            else:
                if verbose:
                    print("Warning: Failed to download VIX data")

        if verbose:
            print("\n" + "=" * 50)
            print(f"Download complete: {successful}/{total} symbols successful")
            print(f"Failed: {len(failed)} symbols")
            if failed and len(failed) <= 20:
                print("\nFailed symbols:")
                for sym, reason in failed[:20]:
                    print(f"  {sym}: {reason}")

        return self.stock_data

    def save_data(self, filename: str = 'stock_data.pkl') -> None:
        """
        Save downloaded data to disk.

        Args:
            filename: Output filename
        """
        filepath = os.path.join(self.data_dir, filename)
        data = {
            'stock_data': self.stock_data,
            'vix_data': self.vix_data,
            'metadata': self.metadata,
            'params': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'min_price': self.min_price,
                'min_volume': self.min_volume
            }
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"Data saved to {filepath}")

    def load_data(self, filename: str = 'stock_data.pkl') -> bool:
        """
        Load previously downloaded data from disk.

        Args:
            filename: Input filename

        Returns:
            True if load successful
        """
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            self.stock_data = data['stock_data']
            self.vix_data = data.get('vix_data')
            self.metadata = data.get('metadata', {})
            print(f"Data loaded from {filepath}")
            print(f"Loaded {len(self.stock_data)} symbols")
            return True
        except Exception as e:
            print(f"Failed to load data: {str(e)}")
            return False

    def get_market_regime(self) -> pd.DataFrame:
        """
        Calculate market regime based on SPY trend and VIX levels.

        Returns:
            DataFrame with regime classification
        """
        if 'SPY' not in self.stock_data:
            raise ValueError("SPY data required for market regime calculation")

        spy_df = self.stock_data['SPY'].copy()

        # Calculate SPY trend (using 50-day SMA)
        spy_df['sma_50'] = spy_df['close'].rolling(50).mean()
        spy_df['sma_200'] = spy_df['close'].rolling(200).mean()
        spy_df['spy_uptrend'] = spy_df['close'] > spy_df['sma_50']
        spy_df['spy_bullish'] = spy_df['sma_50'] > spy_df['sma_200']

        # Add VIX data
        if self.vix_data is not None:
            vix_aligned = self.vix_data['close'].reindex(spy_df.index).ffill()
            spy_df['vix'] = vix_aligned
        else:
            # Estimate VIX from SPY volatility
            spy_df['vix'] = spy_df['close'].pct_change().rolling(20).std() * np.sqrt(252) * 100

        # Classify regime
        def classify_regime(row):
            if pd.isna(row['vix']) or pd.isna(row['sma_50']):
                return 'Unknown'

            vix = row['vix']
            uptrend = row['spy_uptrend']

            if vix > 30:
                return 'High Volatility'
            elif vix > 25 and not uptrend:
                return 'Bear Market'
            elif vix < 20 and uptrend:
                return 'Bull Market'
            else:
                return 'Neutral'

        spy_df['regime'] = spy_df.apply(classify_regime, axis=1)

        return spy_df[['close', 'sma_50', 'sma_200', 'vix', 'regime']]

    def get_data_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for all loaded data.

        Returns:
            Summary DataFrame
        """
        summary_data = []

        for symbol, df in self.stock_data.items():
            summary_data.append({
                'symbol': symbol,
                'start_date': df.index.min(),
                'end_date': df.index.max(),
                'trading_days': len(df),
                'avg_price': df['close'].mean(),
                'avg_volume': df['volume'].mean(),
                'avg_dollar_volume': (df['close'] * df['volume']).mean(),
                'total_return': (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100,
                'volatility': df['close'].pct_change().std() * np.sqrt(252) * 100
            })

        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('avg_dollar_volume', ascending=False)

        return summary_df

    def align_data_to_dates(self, start: str = None, end: str = None) -> Dict[str, pd.DataFrame]:
        """
        Align all stock data to common date range.

        Args:
            start: Start date (optional)
            end: End date (optional)

        Returns:
            Dictionary of aligned DataFrames
        """
        if not self.stock_data:
            return {}

        # Find common date range
        all_dates = set()
        for symbol, df in self.stock_data.items():
            all_dates.update(df.index.tolist())
        all_dates = sorted(all_dates)

        if start:
            all_dates = [d for d in all_dates if d >= pd.Timestamp(start)]
        if end:
            all_dates = [d for d in all_dates if d <= pd.Timestamp(end)]

        date_index = pd.DatetimeIndex(all_dates)

        aligned_data = {}
        for symbol, df in self.stock_data.items():
            aligned_df = df.reindex(date_index)
            aligned_df = aligned_df.ffill().bfill()
            aligned_data[symbol] = aligned_df

        return aligned_data


def main():
    """Main function to download and save stock data."""
    # Initialize data loader
    loader = DataLoader(
        data_dir='data',
        start_date='2015-01-01',
        end_date='2025-01-01',
        min_price=5.0,
        min_volume=50_000_000
    )

    # Try to load existing data first
    if loader.load_data():
        print("\nUsing cached data")
    else:
        print("\nDownloading fresh data...")
        loader.download_all_stocks(verbose=True)
        loader.save_data()

    # Print summary
    print("\n" + "=" * 60)
    print("DATA SUMMARY")
    print("=" * 60)

    summary = loader.get_data_summary()
    print(f"\nTotal symbols loaded: {len(summary)}")
    print(f"\nTop 10 by dollar volume:")
    print(summary.head(10)[['symbol', 'trading_days', 'avg_price', 'avg_dollar_volume', 'total_return']].to_string())

    # Print market regime info
    print("\n" + "=" * 60)
    print("MARKET REGIME ANALYSIS")
    print("=" * 60)

    try:
        regime_df = loader.get_market_regime()
        regime_counts = regime_df['regime'].value_counts()
        print("\nRegime distribution:")
        for regime, count in regime_counts.items():
            pct = count / len(regime_df) * 100
            print(f"  {regime}: {count} days ({pct:.1f}%)")
    except Exception as e:
        print(f"Could not calculate market regime: {e}")

    return loader


if __name__ == '__main__':
    main()

import yfinance as yf
import pandas as pd
import sys
import os

# Ensure config is accessible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def _format_yfinance_df(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Helper formatting function for raw yfinance DataFrame."""
    if df.empty:
        return pd.DataFrame()
        
    df = df.reset_index()
    # Handle potentially different index names (Datetime for intraday, Date for daily)
    time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
    df = df.rename(columns={
        time_col: 'timestamp', 
        'Open': 'open', 
        'High': 'high', 
        'Low': 'low', 
        'Close': 'close', 
        'Volume': 'volume'
    })
    
    # Normalize timestamp to UTC
    if df['timestamp'].dt.tz is not None:
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
    else:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        
    df['ticker'] = ticker
    
    # Prune unneeded columns (e.g., Dividends, Stock Splits)
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'ticker']]

def fetch_historical(ticker: str, config: Config) -> pd.DataFrame:
    """Pull 60 days of 1-minute OHLCV data. 
    Note: yfinance might restrict 1m data heavily (often 7 days limit).
    This function delegates the exact config parameters to yfinance.
    """
    ticker_obj = yf.Ticker(ticker)
    
    # Depending on yfinance API limits, "60d" with "1m" might fail or truncate.
    df = ticker_obj.history(period=config.HISTORICAL_PERIOD, interval=config.INTERVAL)
    
    return _format_yfinance_df(df, ticker)

def fetch_latest_bars(ticker: str, n_bars: int, config: Config) -> pd.DataFrame:
    """Pull the most recent n_bars from yfinance for quasi-live mode."""
    ticker_obj = yf.Ticker(ticker)
    
    # '5d' is a safe period to pull to ensure we get enough 1-minute bars
    # given market closes, weekends, and holidays.
    df = ticker_obj.history(period="5d", interval=config.INTERVAL)
    df = _format_yfinance_df(df, ticker)
    
    if df.empty:
        return df
        
    return df.tail(n_bars).reset_index(drop=True)

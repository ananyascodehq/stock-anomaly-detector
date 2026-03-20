import yfinance as yf
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

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
    """Pull historical OHLCV data. 
    Note: yfinance restricts 1m data to 8 days per request. 
    If 1m is requested for a long period, we fetch in chunks.
    """
    ticker_obj = yf.Ticker(ticker)
    
    if config.INTERVAL == "1m":
        # yfinance 1m data limit is ~8 days per call. 
        # We need to fetch in 7-day chunks.
        all_chunks = []
        end_dt = datetime.now()
        
        # 60 days of 1m data = roughly 9 chunks of 7 days
        for i in range(9):
            start_dt = end_dt - timedelta(days=7)
            # Use start/end dates instead of period for 1m chunking
            chunk_df = ticker_obj.history(
                start=start_dt.strftime('%Y-%m-%d'),
                end=end_dt.strftime('%Y-%m-%d'),
                interval="1m"
            )
            if not chunk_df.empty:
                all_chunks.insert(0, _format_yfinance_df(chunk_df, ticker))
            
            end_dt = start_dt
            
        if not all_chunks:
            return pd.DataFrame()
            
        return pd.concat(all_chunks).drop_duplicates('timestamp').sort_values('timestamp')
    else:
        # For larger intervals (1h, 1d), 'period' works fine for 60d
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

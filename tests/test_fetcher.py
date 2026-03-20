import pytest
import pandas as pd
from datetime import datetime
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.fetcher import fetch_historical, fetch_latest_bars
from config import Config

def test_fetch_latest_bars():
    config = Config()
    config.INTERVAL = "1m"
    # Use a small n_bars to test parsing and column structures
    df = fetch_latest_bars("AAPL", 5, config)
    
    assert not df.empty, "DataFrame should not be empty"
    assert len(df) == 5, "Should return exactly 5 bars"
    
    expected_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'ticker']
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column: {col}"
        
    assert df['ticker'].iloc[0] == "AAPL", "Ticker name should match"
    
    # Check timestamp is timezone-aware UTC
    assert str(df['timestamp'].dt.tz) == 'UTC', "Timestamp must be UTC"

def test_fetch_historical():
    config = Config()
    config.HISTORICAL_PERIOD = "1d" # short period just to verify it runs
    config.INTERVAL = "1m"
    df = fetch_historical("AAPL", config)
    
    assert not df.empty, "Historical dataframe should not be empty"
    assert 'timestamp' in df.columns
    assert str(df['timestamp'].dt.tz) == 'UTC'

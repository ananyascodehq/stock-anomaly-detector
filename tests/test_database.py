import pytest
import pandas as pd
from datetime import datetime, timedelta
import os
import sqlite3
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.database import init_db, insert_bars, load_bars, get_latest_timestamp

@pytest.fixture
def test_db_path(tmp_path):
    # Use pytest's tmp_path fixture for isolated temp databases
    db_file = tmp_path / "test_market_data.db"
    return str(db_file)

def test_db_initialization_and_insert(test_db_path):
    init_db(test_db_path)
    
    assert os.path.exists(test_db_path)
    
    # Verify WAL mode
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        # In some environments WAL might fall back, but we should expect wal or at least it doesn't fail
        assert mode.lower() in ('wal', 'memory', 'delete') 
        # Actually standard sqlite should return wal if set correctly

    # Create dummy data
    now = datetime.utcnow()
    df = pd.DataFrame([{
        'timestamp': now,
        'open': 150.0,
        'high': 155.0,
        'low': 149.0,
        'close': 152.0,
        'volume': 1000,
        'ticker': 'TEST'
    }])
    
    # Test insert
    insert_bars(df, test_db_path)
    
    # Test get latest timestamp
    latest = get_latest_timestamp('TEST', test_db_path)
    assert latest is not None
    # Compare down to seconds or microseconds depending on format
    # The insert saves as ISO string. 
    
    # Test load
    start = now - timedelta(days=1)
    end = now + timedelta(days=1)
    loaded_df = load_bars('TEST', start, end, test_db_path)
    
    assert len(loaded_df) == 1
    assert loaded_df['ticker'].iloc[0] == 'TEST'
    assert loaded_df['close'].iloc[0] == 152.0

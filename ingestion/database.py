import sqlite3
import pandas as pd
from typing import Optional
from datetime import datetime

def init_db(db_path: str) -> None:
    """Create tables if not exist. Enable WAL mode."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv (
            ticker      TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            open        REAL,
            high        REAL,
            low         REAL,
            close       REAL,
            volume      REAL,
            PRIMARY KEY (ticker, timestamp)
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker          TEXT NOT NULL,
            timestamp       TEXT NOT NULL,
            zscore_score    REAL,
            if_score        REAL,
            lstm_score      REAL,
            ensemble_score  REAL,
            is_flagged      INTEGER,
            created_at      TEXT DEFAULT (datetime('now'))
        );
        """)
        conn.commit()

def insert_bars(df: pd.DataFrame, db_path: str) -> None:
    """Upsert OHLCV bars. Primary key: (ticker, timestamp)."""
    if df is None or df.empty:
        return
    
    with sqlite3.connect(db_path) as conn:
        records = []
        for _, row in df.iterrows():
            # Format timestamp safely as ISO string
            ts = row['timestamp']
            if isinstance(ts, pd.Timestamp):
                ts_str = ts.isoformat()
            else:
                ts_str = str(ts)
                
            records.append((
                str(row['ticker']),
                ts_str,
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume'])
            ))
            
        conn.executemany("""
            INSERT OR REPLACE INTO ohlcv (ticker, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, records)
        conn.commit()

def load_bars(ticker: str, start: datetime, end: datetime, db_path: str) -> pd.DataFrame:
    """Load bars for a ticker within a time range. Returns DataFrame."""
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT timestamp, open, high, low, close, volume, ticker
            FROM ohlcv
            WHERE ticker = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        """
        start_str = start.isoformat() if isinstance(start, datetime) else str(start)
        end_str = end.isoformat() if isinstance(end, datetime) else str(end)
        
        df = pd.read_sql_query(query, conn, params=(ticker, start_str, end_str))
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

def get_latest_timestamp(ticker: str, db_path: str) -> Optional[datetime]:
    """Return the most recent timestamp stored for a ticker. Used for cache check."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(timestamp) FROM ohlcv WHERE ticker = ?
        """, (ticker,))
        result = cursor.fetchone()
        
        if result and result[0]:
            return pd.to_datetime(result[0]).to_pydatetime()
        return None

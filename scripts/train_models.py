"""
scripts/train_models.py

Standalone script to train all anomaly detection models on historical data.
1. Fetches historical OHLCV data for all tickers.
2. Persists data to SQLite.
3. Computes features.
4. Trains Z-Score, Isolation Forest, and LSTM Autoencoder.
5. Saves trained models to data/models/.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Ensure we're running from the project root
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from config import Config
from ingestion.fetcher import fetch_historical
from ingestion.database import init_db, insert_bars, load_bars
from features.engineer import compute_features
from models.zscore_detector import ZScoreDetector
from models.isolation_forest import IsolationForest
from models.lstm_autoencoder import LSTMAutoencoder

def train_all():
    config = Config()
    
    # 1. Initialize DB and Create Directories
    print("[TRAIN] Initializing system...")
    init_db(config.DB_PATH)
    os.makedirs(config.MODEL_SAVE_PATH, exist_ok=True)
    
    # 2. Fetch and Store Data
    print(f"[TRAIN] Fetching {config.HISTORICAL_PERIOD} historical data for {config.TICKERS}...")
    for ticker in config.TICKERS:
        df = fetch_historical(ticker, config)
        if not df.empty:
            print(f"[TRAIN] Storing {len(df)} bars for {ticker}...")
            insert_bars(df, config.DB_PATH)
        else:
            print(f"[WARNING] No historical data found for {ticker}")

    # 3. Load Data and Compute Features
    # We'll train on one ticker at a time or aggregate? 
    # Usually models are trained per-ticker or on a global pool.
    # The PRD implies training on historical data for all configured tickers.
    all_features = []
    
    start_time = datetime.utcnow() - timedelta(days=70) # extra buffer
    end_time = datetime.utcnow()

    print("[TRAIN] Computing features for training pool...")
    for ticker in config.TICKERS:
        df = load_bars(ticker, start_time, end_time, config.DB_PATH)
        if df.empty:
            continue
            
        features_df = compute_features(df, window=config.FEATURE_WINDOW, rsi_period=config.RSI_PERIOD)
        
        # Feature matrix columns per PRD Layer 2
        feature_cols = [
            'log_return', 'rolling_mean_return', 'rolling_std_return', 
            'volume_zscore', 'price_volume_divergence', 'rsi_14', 
            'vwap_deviation', 'spread_proxy'
        ]
        
        all_features.append(features_df[feature_cols])

    if not all_features:
        print("[ERROR] No features computed. Training aborted.")
        return

    X_train = pd.concat(all_features).values
    print(f"[TRAIN] Training pool size: {X_train.shape}")

    # 4. Train Models
    
    # Z-Score
    print("[TRAIN] Fitting Z-Score Detector...")
    zscore = ZScoreDetector()
    zscore.fit(X_train)
    zscore.save(os.path.join(config.MODEL_SAVE_PATH, "zscore"))

    # Isolation Forest
    print("[TRAIN] Fitting Isolation Forest...")
    iso_forest = IsolationForest()
    iso_forest.fit(X_train)
    iso_forest.save(os.path.join(config.MODEL_SAVE_PATH, "isolation_forest"))

    # LSTM Autoencoder
    print("[TRAIN] Fitting LSTM Autoencoder (this may take a few minutes)...")
    lstm = LSTMAutoencoder()
    lstm.fit(X_train)
    lstm.save(os.path.join(config.MODEL_SAVE_PATH, "lstm"))

    print(f"[SUCCESS] All models saved to {config.MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_all()

"""
scripts/run_dashboard.py

Entry point to launch the full system: background polling loop + Dash app.
Loads trained models, starts inference polling in a daemon thread,
and serves the Dash dashboard.
"""

import sys
import os
import time
import threading

# Ensure we're running from the project root
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from config import Config
from ingestion.fetcher import fetch_latest_bars
from ingestion.database import init_db, insert_bars
from features.engineer import compute_features
from models.zscore_detector import ZScoreDetector
from models.isolation_forest import IsolationForest
from models.lstm_autoencoder import LSTMAutoencoder
from models.ensemble import combine
from alerts.notifier import fire_alert
from dashboard.app import create_app


def load_all_models(config: Config) -> dict:
    """Load all trained models from disk."""
    models = {}

    zscore = ZScoreDetector()
    zscore.load(os.path.join(config.MODEL_SAVE_PATH, "zscore"))
    models["zscore"] = zscore

    iso_forest = IsolationForest()
    iso_forest.load(os.path.join(config.MODEL_SAVE_PATH, "isolation_forest"))
    models["isolation_forest"] = iso_forest

    lstm = LSTMAutoencoder()
    lstm.load(os.path.join(config.MODEL_SAVE_PATH, "lstm"))
    models["lstm"] = lstm

    return models


last_processed_timestamps = {}

def run_inference_pipeline(ticker: str, models: dict, config: Config) -> None:
    """Run the full inference pipeline for a single ticker."""
    import sqlite3
    import pandas as pd
    import numpy as np

    try:
        global last_processed_timestamps
        # 1. Fetch latest bars (need at least ~60 for features + LSTM)
        df = fetch_latest_bars(ticker, n_bars=100, config=config)
        if df is None or df.empty:
            return
            
        latest_ts = str(df.iloc[-1]['timestamp'])

        # 2. Check for synthetic injection flag
        flag_file = os.path.join(os.path.dirname(__file__), "..", f"inject_{ticker}.flag")
        is_synthetic = False
        if os.path.exists(flag_file):
            print(f"[INJECTOR] 🚨 Synthetic Flash Crash applied to {ticker} 🚨")
            is_synthetic = True
            # Force a massive 15% price crash and 50x volume surge on the newest row
            df.iloc[-1, df.columns.get_loc("close")] *= 0.85
            df.iloc[-1, df.columns.get_loc("volume")] *= 50.0
            try:
                os.remove(flag_file)
            except Exception:
                pass
        else:
            # Prevent duplicate model inference when the stock market is closed
            # (yfinance returns the static Friday final minute over and over).
            if last_processed_timestamps.get(ticker) == latest_ts:
                # Still update DB so any previous synthetic mutations are overwritten
                insert_bars(df, config.DB_PATH)
                return
                
        last_processed_timestamps[ticker] = latest_ts

        # 3. Insert into DB
        insert_bars(df, config.DB_PATH)

        # 3. Compute features
        features_df = compute_features(
            df, window=config.FEATURE_WINDOW, rsi_period=config.RSI_PERIOD
        )
        if features_df.empty:
            return

        # 4. Get feature matrix (last row for inference)
        feature_cols = [
            "log_return", "rolling_mean_return", "rolling_std_return",
            "volume_zscore", "price_volume_divergence", "rsi_14",
            "vwap_deviation", "spread_proxy",
        ]
        X = features_df[feature_cols].values

        # 5. Score with each model
        zscore_score = float(models["zscore"].score(X)[-1])
        if_score = float(models["isolation_forest"].score(X)[-1])
        lstm_score = float(models["lstm"].score(X)[-1])

        # 6. Ensemble combine
        scores = {
            "zscore": zscore_score,
            "isolation_forest": if_score,
            "lstm": lstm_score,
        }
        result = combine(scores, config.ENSEMBLE_WEIGHTS, config.ENSEMBLE_MIN_AGREEING_MODELS)

        # 7. Log to anomaly_log table
        timestamp = str(df.loc[features_df.index[-1], 'timestamp'])
        db_ticker = f"{ticker} (TEST)" if is_synthetic else ticker
        
        with sqlite3.connect(config.DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO anomaly_log
                (ticker, timestamp, zscore_score, if_score, lstm_score, ensemble_score, is_flagged)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    db_ticker, timestamp,
                    zscore_score, if_score, lstm_score,
                    result["ensemble_score"],
                    1 if result["is_flagged"] else 0,
                ),
            )

        # 8. Fire alert if flagged
        if result["is_flagged"]:
            alert_scores = {
                "ensemble_score": result["ensemble_score"],
                "zscore": zscore_score,
                "if_score": if_score,
                "lstm_score": lstm_score,
            }
            fire_alert(ticker, timestamp, alert_scores, config)

    except Exception as e:
        print(f"[PIPELINE ERROR] {ticker}: {e}")


def polling_loop(models: dict, config: Config) -> None:
    """Background polling loop — runs inference for all tickers."""
    while True:
        for ticker in config.TICKERS:
            run_inference_pipeline(ticker, models, config)
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    config = Config()

    # Ensure DB is ready
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    init_db(config.DB_PATH)

    # Load trained models
    print("[BOOT] Loading trained models...")
    models = load_all_models(config)
    print("[BOOT] All models loaded.")

    # Start background polling thread
    t = threading.Thread(target=polling_loop, args=(models, config), daemon=True)
    t.start()
    print(f"[BOOT] Polling thread started (interval={config.POLL_INTERVAL_SECONDS}s)")

    # Launch Dash app (blocking)
    app = create_app()
    port = int(os.environ.get("PORT", 10000))
    print(f"[BOOT] Dashboard starting on http://0.0.0.0:{port}/")
    app.run(host="0.0.0.0", port=port)

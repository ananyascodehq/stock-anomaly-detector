import os
from dataclasses import dataclass, field
from typing import List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@dataclass
class Config:
    # Tickers
    TICKERS: List[str] = field(default_factory=lambda: ["AAPL", "SPY", "TSLA"])

    # Data ingestion
    INTERVAL: str = "1m"                  # yfinance bar size
    HISTORICAL_PERIOD: str = "30d"        # Training data window
    POLL_INTERVAL_SECONDS: int = 60       # Live polling frequency

    # Feature engineering
    FEATURE_WINDOW: int = 20              # Rolling window for all features
    RSI_PERIOD: int = 14

    # Model thresholds
    ZSCORE_THRESHOLD: float = 2.5
    IF_CONTAMINATION: float = 0.01        # Isolation Forest expected anomaly rate
    LSTM_RECONSTRUCTION_THRESHOLD: float = 0.02  # MSE threshold

    # Ensemble
    ENSEMBLE_WEIGHTS: dict = field(default_factory=lambda: {
        "zscore": 0.25,
        "isolation_forest": 0.35,
        "lstm": 0.40
    })
    ENSEMBLE_MIN_AGREEING_MODELS: int = 2  # Flag if >= 2 of 3 models agree

    # Anomaly score range: all models output normalized [0.0, 1.0]

    # Dashboard
    DASH_UPDATE_INTERVAL_MS: int = 60000  # dcc.Interval in milliseconds
    DASH_PORT: int = 8050
    DASH_DEBUG: bool = False

    # Alerting
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_SENDER: str = ""
    ALERT_EMAIL_RECIPIENT: str = ""
    ALERT_EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    ALERT_EMAIL_SMTP_PORT: int = 587

    # Paths
    DB_PATH: str = os.path.join(BASE_DIR, "data", "market_data.db")
    MODEL_SAVE_PATH: str = os.path.join(BASE_DIR, "data", "models") + "/"

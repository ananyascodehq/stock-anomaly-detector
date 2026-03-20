# PRD: Real-Time Stock Anomaly Detection System
**Version:** 1.0  
**Status:** Active  
**Type:** Research + Engineering Project  
**Classification:** Academic ML Systems Project

---

## 0. Agent Instructions

This document is the single source of truth for the entire project. Every code file, module, function, and design decision must conform to the specifications herein. Do not infer, improvise, or expand scope beyond what is defined. When ambiguity arises, surface it explicitly rather than silently resolving it. Adhere to the layered architecture — do not mix concerns across layers. All components must be independently testable. Follow the file structure exactly.

### Scope Control (Critical)

- Implement ONLY the explicitly requested file, function, or layer
- Do NOT proceed to other layers, files, or components unless explicitly instructed
- Do NOT anticipate future steps
- Do NOT generate additional modules or helper utilities beyond what is specified
- Any output beyond requested scope is considered INVALID

### No Autonomy Rule

- The agent must not make independent architectural decisions
- The agent must not optimize, refactor, or enhance beyond PRD definitions
- The agent must not modify interfaces, schemas, or function signatures

---

## 1. Project Identity

| Field | Value |
|---|---|
| Project Name | Real-Time Stock Anomaly Detector |
| Primary Goal | Detect statistical anomalies in financial market data using an ensemble of ML models |
| Research Thesis | Ensemble-based anomaly detection outperforms any individual constituent model |
| Evaluation Mode | Proxy evaluation via synthetic anomaly injection + known market event anchors |
| Deployment Target | Local machine (no cloud deployment required) |
| Interface | Plotly Dash web dashboard (localhost) |
| Data Source | Yahoo Finance via `yfinance` library |
| Persistence | Local SQLite database (`market_data.db`) |

---

## 2. Technology Stack

| Component | Library / Tool | Version |
|---|---|---|
| Language | Python | 3.10+ |
| Data Ingestion | yfinance | latest stable |
| Data Storage | SQLite via sqlite3 (stdlib) | — |
| Feature Engineering | pandas, numpy | latest stable |
| ML Model 1 | scipy (Z-score) | latest stable |
| ML Model 2 | scikit-learn (Isolation Forest) | latest stable |
| ML Model 3 | TensorFlow / Keras (LSTM Autoencoder) | 2.x |
| Dashboard | Plotly Dash | latest stable |
| Visualization | plotly.graph_objects | latest stable |
| Alerting | smtplib (stdlib) | — |
| Scheduling / Polling | dcc.Interval (Dash-native) | — |
| Config Management | Python dataclass or `.env` via python-dotenv | latest stable |
| Testing | pytest | latest stable |

**Constraints:**
- No WebSocket server. Dash `dcc.Interval` handles all polling.
- No cloud APIs, no paid data feeds. `yfinance` only.
- No Docker required. Pure Python environment.
- SQLite only. No PostgreSQL, Redis, or external databases.

---

## 3. Project File Structure

```
stock_anomaly_detector/
|
+-- PRD.md                          # This document
+-- README.md                       # Setup and run instructions
+-- requirements.txt                # All pip dependencies
+-- config.py                       # Central configuration (dataclass)
|
+-- data/
|   +-- market_data.db              # SQLite database (auto-created on first run)
|
+-- ingestion/
|   +-- __init__.py
|   +-- fetcher.py                  # yfinance fetch logic (historical + quasi-live)
|   +-- database.py                 # SQLite read/write abstraction layer
|
+-- features/
|   +-- __init__.py
|   +-- engineer.py                 # All 8 features computed here, nothing else
|
+-- models/
|   +-- __init__.py
|   +-- base.py                     # Abstract base class AnomalyDetector
|   +-- zscore_detector.py          # Z-score model
|   +-- isolation_forest.py         # Isolation Forest model
|   +-- lstm_autoencoder.py         # LSTM Autoencoder model
|   +-- ensemble.py                 # Weighted vote combiner
|
+-- evaluation/
|   +-- __init__.py
|   +-- injector.py                 # Synthetic anomaly injection utilities
|   +-- metrics.py                  # Precision, recall, F1 against synthetic labels
|
+-- dashboard/
|   +-- __init__.py
|   +-- app.py                      # Dash app entry point
|   +-- layout.py                   # All Dash layout definitions
|   +-- callbacks.py                # All Dash callback functions
|
+-- alerts/
|   +-- __init__.py
|   +-- notifier.py                 # Console + optional email alerting
|
+-- tests/
|   +-- test_fetcher.py
|   +-- test_features.py
|   +-- test_zscore.py
|   +-- test_isolation_forest.py
|   +-- test_lstm.py
|   +-- test_ensemble.py
|
+-- scripts/
    +-- train_models.py             # Standalone: train all models on historical data
    +-- run_dashboard.py            # Entry point to launch the full system
```

---

## 4. Central Configuration (`config.py`)

All magic numbers and runtime parameters are defined here. No hardcoding in module files.

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    # Tickers
    TICKERS: List[str] = field(default_factory=lambda: ["AAPL", "SPY", "TSLA"])

    # Data ingestion
    INTERVAL: str = "1m"                  # yfinance bar size
    HISTORICAL_PERIOD: str = "60d"        # Training data window
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
    DB_PATH: str = "data/market_data.db"
    MODEL_SAVE_PATH: str = "data/models/"
```

---

## 5. Layer Specifications

### Layer 1 — Data Ingestion

**File:** `ingestion/fetcher.py`

**Responsibilities:**
- Fetch OHLCV data from Yahoo Finance using `yfinance`
- Two fetch modes: `historical` (full 60d training pull) and `live` (latest N bars for inference)
- Never re-fetch data that already exists in SQLite (check by ticker + timestamp range before fetching)

**Function Signatures:**
```python
def fetch_historical(ticker: str, config: Config) -> pd.DataFrame:
    """Pull 60 days of 1-minute OHLCV. Returns DataFrame with columns:
    [timestamp, open, high, low, close, volume, ticker].
    Timestamps are UTC-normalized."""

def fetch_latest_bars(ticker: str, n_bars: int, config: Config) -> pd.DataFrame:
    """Pull the most recent n_bars from yfinance for quasi-live mode.
    Returns same schema as fetch_historical."""
```

**File:** `ingestion/database.py`

```python
def init_db(db_path: str) -> None:
    """Create tables if not exist. Enable WAL mode. Schema below."""

def insert_bars(df: pd.DataFrame, db_path: str) -> None:
    """Upsert OHLCV bars. Primary key: (ticker, timestamp)."""

def load_bars(ticker: str, start: datetime, end: datetime, db_path: str) -> pd.DataFrame:
    """Load bars for a ticker within a time range. Returns DataFrame."""

def get_latest_timestamp(ticker: str, db_path: str) -> Optional[datetime]:
    """Return the most recent timestamp stored for a ticker. Used for cache check."""
```

**SQLite Schema:**
```sql
CREATE TABLE IF NOT EXISTS ohlcv (
    ticker      TEXT NOT NULL,
    timestamp   TEXT NOT NULL,   -- ISO 8601 UTC string
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      REAL,
    PRIMARY KEY (ticker, timestamp)
);

CREATE TABLE IF NOT EXISTS anomaly_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    zscore_score    REAL,
    if_score        REAL,
    lstm_score      REAL,
    ensemble_score  REAL,
    is_flagged      INTEGER,     -- 0 or 1
    created_at      TEXT DEFAULT (datetime('now'))
);

PRAGMA journal_mode=WAL;   -- Required: prevents read/write contention with Dash
```

---

### Layer 2 — Feature Engineering

**File:** `features/engineer.py`

**Single public function:**
```python
def compute_features(df: pd.DataFrame, window: int = 20, rsi_period: int = 14) -> pd.DataFrame:
    """
    Input:  DataFrame with columns [timestamp, open, high, low, close, volume]
            sorted ascending by timestamp.
    Output: DataFrame with 8 feature columns. Rows with insufficient history
            (first `window` rows) are dropped. Do not forward-fill or impute.
    Raises: ValueError if input has fewer than (window + rsi_period) rows.
    """
```

**8 Features — Exact Definitions:**

| # | Feature Name | Formula | Notes |
|---|---|---|---|
| 1 | `log_return` | `ln(close_t / close_{t-1})` | Per-bar log return |
| 2 | `rolling_mean_return` | `mean(log_return, window)` | Rolling mean over `window` bars |
| 3 | `rolling_std_return` | `std(log_return, window)` | Realized volatility proxy |
| 4 | `volume_zscore` | `(volume - rolling_mean(volume, window)) / rolling_std(volume, window)` | Volume deviation from norm |
| 5 | `price_volume_divergence` | `log_return / (volume_zscore + 1e-9)` | Epsilon prevents divide-by-zero |
| 6 | `rsi_14` | Wilder RSI over `rsi_period` bars | Normalized [0, 100] |
| 7 | `vwap_deviation` | `(close - vwap) / vwap` where `vwap = sum(close*volume, window) / sum(volume, window)` | Rolling VWAP deviation |
| 8 | `spread_proxy` | `(high - low) / close` | Normalized intraday range |

**Constraints:**
- All computations use only past data (no lookahead bias).
- Output column order must be fixed and match the table above for model compatibility.
- Output dtype: `float64` for all feature columns.
- Assert `feature_df.isnull().sum().sum() == 0` before returning. Raise `ValueError` if NaN present.

---

### Layer 3 — Anomaly Detection Models

#### Abstract Base Class (`models/base.py`)

```python
from abc import ABC, abstractmethod
import numpy as np

class AnomalyDetector(ABC):
    @abstractmethod
    def fit(self, X: np.ndarray) -> None:
        """Train on historical feature matrix. X shape: (n_samples, 8)."""

    @abstractmethod
    def score(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores in [0.0, 1.0] for each row. Shape: (n_samples,)."""

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist model to disk."""

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model from disk."""
```

All three models must implement this interface without exception.

---

#### Model 1: Z-Score Detector (`models/zscore_detector.py`)

**Algorithm:** Composite Z-score across all features compared to training distribution.

**fit():** Compute and store per-feature `mean` and `std` from training data.

**score():**
```
raw_z    = max(|feature_i - mean_i| / std_i)   for i in 1..8
score    = sigmoid(raw_z - ZSCORE_THRESHOLD)
```
Sigmoid shifts so that `raw_z == ZSCORE_THRESHOLD` maps to score ~0.5.

**Flag threshold:** `score > 0.5`

**Persistence:** `numpy.save` / `numpy.load` for mean/std arrays.

---

#### Model 2: Isolation Forest (`models/isolation_forest.py`)

**Algorithm:** `sklearn.ensemble.IsolationForest`

**Hyperparameters:**
```python
IsolationForest(
    n_estimators=200,
    contamination=Config.IF_CONTAMINATION,  # 0.01
    max_samples="auto",
    random_state=42
)
```

**Score normalization:**
sklearn returns raw scores in approximately [-0.5, 0.5].
```
normalized_score = 1 - (raw_score + 0.5)
```
Higher normalized score = more anomalous.

**Flag threshold:** `normalized_score > 0.6`

**Persistence:** `joblib.dump` / `joblib.load`

---

#### Model 3: LSTM Autoencoder (`models/lstm_autoencoder.py`)

**Algorithm:** Sequence reconstruction. Anomaly score = reconstruction MSE.

**Architecture:**
```
Input:   (batch_size, sequence_length=20, n_features=8)

Encoder: LSTM(64, return_sequences=False, activation='tanh')
         RepeatVector(20)

Decoder: LSTM(64, return_sequences=True, activation='tanh')
         TimeDistributed(Dense(8))

Loss:    MSE
Optimizer: Adam(lr=0.001)
```

**Training parameters:**
```python
model.fit(
    X_seq, X_seq,       # autoencoder: input == target
    epochs=50,
    batch_size=32,
    validation_split=0.1,
    callbacks=[EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)]
)
```

**Input preparation:** Build sliding window sequences of length 20 from the feature matrix.

**score():**
```
mse_per_sample = mean((X_reconstructed - X_input)^2, axis=(1,2))
normalized     = min(mse_per_sample / (2 * LSTM_RECONSTRUCTION_THRESHOLD), 1.0)
```

**Flag threshold:** `normalized_score > 0.5`

**Persistence:** `model.save(path)` / `tf.keras.models.load_model(path)`

---

#### Ensemble Combiner (`models/ensemble.py`)

**Algorithm:** Weighted linear combination with majority agreement gate.

```python
def combine(scores: dict, weights: dict, min_agreeing: int = 2) -> dict:
    """
    Input:
        scores:        {"zscore": float, "isolation_forest": float, "lstm": float}
        weights:       Config.ENSEMBLE_WEIGHTS
        min_agreeing:  Config.ENSEMBLE_MIN_AGREEING_MODELS

    Returns:
        {
            "ensemble_score":  float,   # weighted average of all 3 scores
            "is_flagged":      bool,    # True if ensemble_score > 0.5 AND len(agreeing) >= min_agreeing
            "agreeing_models": list     # model names that individually crossed their threshold
        }
    """
```

**Individual flag thresholds used inside combine():**

| Model | Flag if score > |
|---|---|
| zscore | 0.5 |
| isolation_forest | 0.6 |
| lstm | 0.5 |

**Flag logic:**
```python
ensemble_score = sum(scores[m] * weights[m] for m in scores)
agreeing       = [m for m in scores if individual_threshold_exceeded(m, scores[m])]
is_flagged     = (ensemble_score > 0.5) and (len(agreeing) >= min_agreeing)
```

---

### Layer 4 — Dashboard

**Files:** `dashboard/app.py`, `dashboard/layout.py`, `dashboard/callbacks.py`

#### Layout — Required Panels

| Panel | Dash Component | Spec |
|---|---|---|
| Price Chart | `dcc.Graph` (id: `price-chart`) | Line chart with red dot markers at anomaly timestamps |
| Anomaly Score Gauge | `dcc.Graph` (id: `score-gauge`) | Indicator/Gauge, range [0, 1], red zone > 0.5 |
| Model Comparison | `dcc.Graph` (id: `model-comparison`) | Grouped bar chart: z, if, lstm scores for latest bar |
| Alert Log Table | `dash_table.DataTable` (id: `alert-table`) | Columns: timestamp, ticker, zscore, if, lstm, ensemble, flagged |
| Ticker Dropdown | `dcc.Dropdown` (id: `ticker-dropdown`) | Options from `Config.TICKERS` |
| Update Interval | `dcc.Interval` (id: `update-interval`) | `interval=Config.DASH_UPDATE_INTERVAL_MS` |

#### Callbacks

```
Callback 1 — update_price_chart
  Inputs:  update-interval.n_intervals, ticker-dropdown.value
  Output:  price-chart.figure
  Logic:   Load last 100 ohlcv bars from DB for selected ticker.
           Overlay red markers at timestamps where is_flagged=1 in anomaly_log.

Callback 2 — update_gauge
  Inputs:  update-interval.n_intervals, ticker-dropdown.value
  Output:  score-gauge.figure
  Logic:   Load latest anomaly_log row for ticker. Display ensemble_score.

Callback 3 — update_model_comparison
  Inputs:  update-interval.n_intervals, ticker-dropdown.value
  Output:  model-comparison.figure
  Logic:   Load latest anomaly_log row. Grouped bar: zscore_score, if_score, lstm_score.

Callback 4 — update_alert_table
  Inputs:  update-interval.n_intervals
  Output:  alert-table.data
  Logic:   Load last 50 anomaly_log rows across all tickers. Order by created_at DESC.
```

**Critical constraint:** Callbacks read only from the database. They do not run model inference. Inference runs in the background polling thread (see `scripts/run_dashboard.py`).

---

### Layer 5 — Evaluation Framework

**File:** `evaluation/injector.py`

There are no ground-truth labels in live market data. Synthetic anomaly injection provides a labeled evaluation set.

```python
def inject_price_spike(df: pd.DataFrame, idx: int, magnitude: float = 5.0) -> pd.DataFrame:
    """Multiply close[idx] by (1 + magnitude * rolling_std_at_idx). Label row as anomaly=1."""

def inject_volume_surge(df: pd.DataFrame, idx: int, magnitude: float = 8.0) -> pd.DataFrame:
    """Multiply volume[idx] by magnitude. Label row as anomaly=1."""

def inject_flash_crash(df: pd.DataFrame, idx: int, drop_pct: float = 0.03) -> pd.DataFrame:
    """Drop close[idx] by drop_pct fraction, recover at idx+1. Label both rows anomaly=1."""

def create_labeled_dataset(
    df: pd.DataFrame,
    anomaly_rate: float = 0.02,
    seed: int = 42
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Randomly inject anomalies at anomaly_rate fraction of rows.
    Returns (modified_df, binary_labels array of shape (n_rows,)).
    """
```

**File:** `evaluation/metrics.py`

```python
def evaluate_detector(
    detector: AnomalyDetector,
    X: np.ndarray,
    y_true: np.ndarray,
    flag_threshold: float
) -> dict:
    """
    Returns:
    {
        "precision":                  float,
        "recall":                     float,
        "f1":                         float,
        "false_positive_rate":        float,
        "auc_roc":                    float,
        "avg_detection_latency_bars": float  # mean bars between injection index and first flag
    }
    """
```

Evaluation must be run for each individual model AND the ensemble. Populate Section 10 results table.

---

### Layer 6 — Alerting

**File:** `alerts/notifier.py`

```python
def fire_alert(ticker: str, timestamp: str, scores: dict, config: Config) -> None:
    """
    Always:                     Print structured alert to stdout.
    If email enabled:           Send via smtplib TLS.

    Console format:
    [ANOMALY] {timestamp} | {ticker} | ensemble={ensemble_score:.3f} |
    z={zscore:.3f} | if={if_score:.3f} | lstm={lstm_score:.3f}
    """
```

**Email spec:**
- Subject: `[ANOMALY ALERT] {ticker} @ {timestamp}`
- Body: Plain text. All 4 scores. Disclaimer (below). No HTML.

**Required disclaimer — must appear in ALL alert outputs:**
```
DISCLAIMER: This alert represents a statistical deviation from historical patterns
detected by an automated ML system. It does not constitute financial advice, a
trading signal, or a prediction of future price movement. Do not make investment
decisions based on this output.
```

---

## 6. End-to-End Data Flow

```
TRAINING PHASE (scripts/train_models.py — run once)
  |
  +-- fetch_historical(tickers) --> insert_bars(db)
  |
  +-- load_bars(db) --> compute_features()
  |
  +-- fit(zscore_detector)
  +-- fit(isolation_forest)
  +-- fit(lstm_autoencoder)
  |
  +-- save all models to data/models/

RUNTIME PHASE (scripts/run_dashboard.py)
  |
  +-- load all trained models from data/models/
  |
  +-- Launch Dash app (non-blocking, separate thread)
  |
  +-- Background polling loop (main thread, every 60s):
        for ticker in TICKERS:
          fetch_latest_bars(ticker, n=FEATURE_WINDOW+1)
          insert_bars(db)
          compute_features()
          zscore_score  = zscore_detector.score(features)
          if_score      = isolation_forest.score(features)
          lstm_score    = lstm_autoencoder.score(features)
          result        = ensemble.combine(scores)
          insert_anomaly_log(db, result)
          if result["is_flagged"]:
              fire_alert(ticker, timestamp, scores)
  |
  +-- Dash callbacks read from DB on each dcc.Interval tick
```

---

## 7. Background Polling Implementation Note

`scripts/run_dashboard.py` must run the polling loop and the Dash server concurrently. Recommended pattern:

```python
import threading

def polling_loop(models, config):
    while True:
        for ticker in config.TICKERS:
            run_inference_pipeline(ticker, models, config)
        time.sleep(config.POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    models = load_all_models(config)
    t = threading.Thread(target=polling_loop, args=(models, config), daemon=True)
    t.start()
    app.run_server(port=config.DASH_PORT, debug=config.DASH_DEBUG)
```

SQLite WAL mode (set in `init_db`) ensures the polling thread and Dash callbacks do not block each other.

---

## 8. Out of Scope

Do not implement:

- Real brokerage API integration (Alpaca, Interactive Brokers, etc.)
- Actual buy/sell signal generation or backtesting
- Portfolio management or position sizing
- WebSocket-based live streaming
- Cloud deployment or containerization
- User authentication on the dashboard
- Multi-timeframe analysis (1-minute bars only)
- Sentiment analysis or alternative data sources
- Any paid data feed

---

## 9. Known Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| yfinance rate limiting or data gaps | Incomplete training data | Retry with exponential backoff; log missing windows; do not crash |
| LSTM overfitting on limited 1m data | Poor generalization at inference | EarlyStopping + val split; monitor val_loss not train_loss |
| No ground-truth anomaly labels | Cannot compute true precision/recall | Synthetic injection (Section 5); known event anchors as manual validation |
| Market hours dependency | No new bars during off-hours or weekends | Detect closed market (no new timestamp from yfinance); log and skip gracefully |
| SQLite read/write contention | Race conditions between polling and Dash | WAL mode enabled in init_db |
| Feature NaN propagation | Silent model failures on corrupt scores | Assert no NaN post-feature-engineering; log and skip bar if NaN present |
| LSTM sequence warmup gap | First 20 bars cannot be scored | Log clearly; do not insert partial scores into anomaly_log |

---

## 10. Success Criteria

The project is complete when all of the following conditions are satisfied:

- [ ] All 3 models train successfully on 60 days of 1-minute OHLCV for all configured tickers
- [ ] Feature matrix has zero NaN values at inference time (post warmup period)
- [ ] Ensemble F1 score strictly exceeds every individual model F1 on synthetic labeled dataset
- [ ] Dashboard renders all 4 panels and updates every 60s without crashing
- [ ] Anomaly log persists correctly across dashboard restarts (DB survives process restart)
- [ ] At least one known market event is visibly flagged in historical replay
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Alert fires (console minimum) on every flagged bar
- [ ] Disclaimer appears in all alert outputs

---

## 11. Evaluation Results Table (populate after evaluation run)

This table is the quantitative core of the research claim. It must be produced by `evaluation/metrics.py` and included in the project report.

| Model | Precision | Recall | F1 | FPR | AUC-ROC |
|---|---|---|---|---|---|
| Z-Score | — | — | — | — | — |
| Isolation Forest | — | — | — | — | — |
| LSTM Autoencoder | — | — | — | — | — |
| **Ensemble** | — | — | — | — | — |

The ensemble row must show the highest F1 and lowest FPR to substantiate the research thesis.

---

*End of PRD v1.0*

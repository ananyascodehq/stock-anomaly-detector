# Project Status & Technical Specification
**Project:** Stock Anomaly Detector  
**Status:** Active / Operational  

---

## 1. Comprehensive Overview
The **Stock Anomaly Detector** is a high-performance, real-time telemetry system designed to flag unusual market behavior (e.g., flash crashes, volume surges, price-volume divergence). It integrates live market data ingestion with a multi-model Machine Learning pipeline, distilling technical indicators into a single actionable anomaly score.

The system is split into two primary operational modes:
1. **Offline Training**: Historical data ingestion and model training (`scripts/train_models.py`).
2. **Live Telemetry & Dashboard**: Real-time minute-by-minute data polling, background inference, and a web-based interactive UI (`scripts/run_dashboard.py`).

---

## 2. Technical Architecture & Specification

### 2.1 Core Infrastructure
- **Language Supported**: Python 3.10+
- **Database**: Local SQLite (`data/market_data.db`) for persisting OHLCV bars, engineered features, and anomaly logs.
- **Frontend Dashboard**: Dash / Plotly (Flask-based web server).
- **Data Source**: Yahoo Finance (1-minute interval OHLCV polling).

### 2.2 The Ensemble AI Pipeline
The "Brain" of the system relies on three parallel algorithms, normalized to output an anomaly score between `[0.0, 1.0]`. An event is officially flagged if at least **2 out of 3 models** agree (score > 0.5).

1. **Z-Score (Statistical)**
   - *Weight*: 25%
   - *Purpose*: Detects sudden, extreme deviations from the rolling historical standard deviation.
   - *Threshold*: Z-Score > 2.5 translates to high anomaly probability.

2. **Isolation Forest (Unsupervised Clustering)**
   - *Weight*: 35%
   - *Purpose*: Analyzes the high-dimensional feature space (RSI, VWAP, Log Returns, etc.) to isolate outliers that don't cluster with typical trading behavior.
   - *Contamination Rate*: Set to 1% (0.01).

3. **LSTM Autoencoder (Deep Learning Sequence tracking)**
   - *Weight*: 40%
   - *Purpose*: Reconstructs chronological market sequences. If a sudden crash or surge occurs, the model fails to reconstruct it from memory, resulting in a high Mean Squared Error (MSE), which indicates a pattern collapse.

### 2.3 Feature Engineering Matrix
All models are driven by a continuous calculation of technical synergy markers based on a 20-minute rolling window:
- Log Returns (Price Momentum)
- VWAP Deviations (Volume Weighted Average Price tracking)
- RSI 14 (Relative Strength Index)
- Price-Volume Divergence Indicators

---

## 3. Product Usage Flow

### Phase 1: Preparation & Training
1. **Initialize Environment**: Start the virtual environment and ensure dependencies in `requirements.txt` are installed.
2. **Train Models**: Execute `python scripts/train_models.py`.
   - The system fetches the last 30 days (`30d`) of 1-minute historical data for defined tickers (e.g., AAPL, SPY, TSLA).
   - The models fit the historical data to understand "normal" market behavior.
   - Serialized `.pkl` or `.h5` models are saved to `data/models/`.

### Phase 2: Live Operations
1. **Launch Engine**: Execute `python scripts/run_dashboard.py`.
   - **Background Polling Cycle**: Every 60 seconds, the engine pulls new 1-minute bars, engineers the features, runs cross-model inference, and saves the results to SQLite.
   - **Web Server Launch**: The interactive Dash UI is spun up at `http://localhost:8050`.

### Phase 3: Dashboard Monitoring & Auditing
1. **Monitor Activity**: Navigate to `http://localhost:8050/`. The dashboard updates automatically. It displays:
   - Live Price Chart overlaying red flagged anomalies.
   - A synchronized Ensemble Score Gauge.
   - A real-time grouped Bar Chart showing individual model scores.
   - A tabular log of recent alerts.
2. **Deep-Dive Logs**: Clicking on any log row opens a modal detailing exactly *why* the mathematical consensus flagged that minute's action.
3. **Synthetic Injector (War Room)**: App administrators can inject a fake anomaly into the live pipeline to audit the system's reaction speed and notification routing.
4. **PDF Export**: Users can export the telemetry log directly into a clean, modern PDF document for record-keeping and auditing.

---

## 4. Repository & Folder Structure

This section outlines the layout of the `stock-anomaly-detector` repository to aid onboarding and collaborator handovers.

```text
stock-anomaly-detector/
│
├── alerts/                 # Warning logic and routing
│   └── (Notification logic such as SMTP email alerts based on config settings)
│
├── dashboard/              # Frontend Dash Application (The Heart)
│   ├── assets/             # CSS styling and static assets 
│   ├── app.py              # Main Flask/Dash app initialization
│   ├── callbacks.py        # All interactive logic, DB polling, and chart rendering
│   ├── layout.py           # Dashboard UI component hierarchy
│   └── pdf_generator.py    # Clean, modern export generator for telemetry logic
│
├── data/                   # Data artifacts and storage layer
│   ├── market_data.db      # SQLite persistence for bars and anomaly logs
│   └── models/             # Serialized (.pkl / .h5) AI models after training
│
├── docs/                   # Internal documentation and guides
│   └── project_status.md   # [You Are Here] Handover and architecture spec
│
├── evaluation/             # Tools/scripts for backtesting and assessing model accuracy
│
├── features/               # Feature engineering pipelines
│   └── (Computes Log Returns, VWAP Deviations, RSI 14, and Price-Volume Divergence)
│
├── ingestion/              # Data sourcing
│   └── (Fetches real-time 1m OHLCV data from Yahoo Finance API)
│
├── models/                 # The Brain: Algorithm classes
│   └── (Implementation of Z-Score, Isolation Forest, and LSTM Autoencoder)
│
├── scripts/                # Entry-point executables
│   ├── run_dashboard.py    # Polls live data, runs inference, and boots the Dash server
│   └── train_models.py     # Batch ingests historical 30d data and trains the models
│
├── tests/                  # PyTest suite for unit and integration testing
│   └── (Verifies ingestion, features, and model outputs)
│
├── config.py               # Global configuration hub (API keys, weights, thresholds)
├── requirements.txt        # Python dependency manifest
└── README.md               # Primary high-level project repository readme
```

### Module Responsibilities Breakdown
- **Config Hub (`config.py`)**: Centralizes the `ENSEMBLE_WEIGHTS`, `ZSCORE_THRESHOLD`, `IF_CONTAMINATION`, and `LSTM_RECONSTRUCTION_THRESHOLD`. It dictates the update intervals for both polling and the dashboard.
- **The Dashboard (`dashboard/`)**: Entirely decoupled from the inference engine. It solely reads from the `data/market_data.db` SQLite instance to display updates seamlessly without executing heavy operations.
- **The Models (`models/`)**: Strictly mathematical implementations handling fit and predict phases without worrying about file I/O or fetching data.
- **The Pipeline (`scripts/`)**: Acts as the orchestrator to pull data via `ingestion/`, mutate it via `features/`, feed it to `models/`, and save it to `data/`.

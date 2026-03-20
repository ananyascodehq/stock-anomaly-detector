"""
dashboard/callbacks.py

All Dash callback functions for the Stock Anomaly Detector dashboard.
Callbacks read ONLY from the SQLite database — no model inference here.
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import Config

config = Config()

# ── Plotly theme constants ──────────────────────────────────────────
PLOT_BG = "rgba(0,0,0,0)"
PAPER_BG = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255, 255, 255, 0.05)"
FONT = dict(color="#a1a1aa", family="Inter, sans-serif")
ACCENT = "#06b6d4"   # neon cyan
DANGER = "#f43f5e"   # rose red
WARN = "#f59e0b"     # amber


def _get_conn():
    """Return a new SQLite connection to the project database."""
    db_path = os.path.join(
        os.path.dirname(__file__), "..", config.DB_PATH
    )
    return sqlite3.connect(db_path)


# ════════════════════════════════════════════════════════════════════
# Callback 1 — update_price_chart
# ════════════════════════════════════════════════════════════════════
@callback(
    Output("price-chart", "figure"),
    Input("update-interval", "n_intervals"),
    Input("ticker-dropdown", "value"),
)
def update_price_chart(n_intervals, ticker):
    """Load last 100 OHLCV bars from DB for selected ticker.
    Overlay red markers at timestamps where is_flagged=1 in anomaly_log."""
    fig = go.Figure()

    try:
        conn = _get_conn()

        # Load last 100 price bars
        bars_df = pd.read_sql_query(
            """
            SELECT timestamp, close FROM ohlcv
            WHERE ticker = ?
            ORDER BY timestamp DESC LIMIT 100
            """,
            conn,
            params=(ticker,),
        )

        # Load flagged anomaly timestamps
        anomalies_df = pd.read_sql_query(
            """
            SELECT timestamp, ensemble_score FROM anomaly_log
            WHERE ticker = ? AND is_flagged = 1
            ORDER BY timestamp DESC LIMIT 100
            """,
            conn,
            params=(ticker,),
        )
        conn.close()

        if not bars_df.empty:
            bars_df = bars_df.sort_values("timestamp")
            fig.add_trace(
                go.Scatter(
                    x=bars_df["timestamp"],
                    y=bars_df["close"],
                    mode="lines",
                    name="Close",
                    line=dict(color=ACCENT, width=2),
                )
            )

        if not anomalies_df.empty:
            # Merge to get close prices at anomaly timestamps
            merged = anomalies_df.merge(bars_df, on="timestamp", how="inner")
            if not merged.empty:
                fig.add_trace(
                    go.Scatter(
                        x=merged["timestamp"],
                        y=merged["close"],
                        mode="markers",
                        name="Anomaly",
                        marker=dict(
                            color=DANGER,
                            size=10,
                            symbol="hexagon",
                            line=dict(width=1, color=DANGER),
                        ),
                    )
                )
    except Exception:
        pass  # Gracefully show empty chart if DB not ready

    fig.update_layout(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=FONT,
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(font=dict(color="#F8FAFC")),
        showlegend=True,
    )
    return fig


# ════════════════════════════════════════════════════════════════════
# Callback 2 — update_gauge
# ════════════════════════════════════════════════════════════════════
@callback(
    Output("score-gauge", "figure"),
    Input("update-interval", "n_intervals"),
    Input("ticker-dropdown", "value"),
)
def update_gauge(n_intervals, ticker):
    """Load latest anomaly_log row for ticker. Display ensemble_score."""
    score = 0.0

    try:
        conn = _get_conn()
        row = pd.read_sql_query(
            """
            SELECT ensemble_score FROM anomaly_log
            WHERE ticker = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            conn,
            params=(ticker,),
        )
        conn.close()
        if not row.empty:
            score = float(row.iloc[0]["ensemble_score"])
    except Exception:
        pass

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number=dict(
                font=dict(color="#F8FAFC", family="Fira Code", size=36)
            ),
            gauge=dict(
                axis=dict(range=[0, 1], tickcolor="#a1a1aa"),
                bar=dict(color=ACCENT if score <= 0.5 else DANGER),
                bgcolor="rgba(24, 24, 27, 0.5)",
                bordercolor="rgba(255, 255, 255, 0.1)",
                steps=[
                    dict(range=[0, 0.5], color="rgba(255, 255, 255, 0.02)"),
                    dict(range=[0.5, 1.0], color="rgba(244, 63, 94, 0.15)"),
                ],
                threshold=dict(
                    line=dict(color=DANGER, width=2),
                    thickness=0.8,
                    value=0.5,
                ),
            ),
        )
    )
    fig.update_layout(
        paper_bgcolor=PLOT_BG,
        font=FONT,
        margin=dict(l=20, r=20, t=30, b=10),
    )
    return fig


# ════════════════════════════════════════════════════════════════════
# Callback 3 — update_model_comparison
# ════════════════════════════════════════════════════════════════════
@callback(
    Output("model-comparison", "figure"),
    Input("update-interval", "n_intervals"),
    Input("ticker-dropdown", "value"),
)
def update_model_comparison(n_intervals, ticker):
    """Load latest anomaly_log row. Grouped bar: zscore, if, lstm scores."""
    scores = {"Z-Score": 0, "Iso Forest": 0, "LSTM": 0}

    try:
        conn = _get_conn()
        row = pd.read_sql_query(
            """
            SELECT zscore_score, if_score, lstm_score FROM anomaly_log
            WHERE ticker = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            conn,
            params=(ticker,),
        )
        conn.close()
        if not row.empty:
            scores["Z-Score"] = float(row.iloc[0]["zscore_score"])
            scores["Iso Forest"] = float(row.iloc[0]["if_score"])
            scores["LSTM"] = float(row.iloc[0]["lstm_score"])
    except Exception:
        pass

    colors = [ACCENT, WARN, "#8B5CF6"]  # green, amber, purple
    fig = go.Figure(
        go.Bar(
            x=list(scores.keys()),
            y=list(scores.values()),
            marker_color=colors,
            text=[f"{v:.2f}" for v in scores.values()],
            textposition="outside",
            textfont=dict(color="#F8FAFC", family="Fira Code", size=12),
        )
    )
    fig.update_layout(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=FONT,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(
            range=[0, 1.1],
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
        ),
        margin=dict(l=30, r=10, t=10, b=30),
    )
    return fig


# ════════════════════════════════════════════════════════════════════
# Callback 4 — update_alert_table
# ════════════════════════════════════════════════════════════════════
@callback(
    Output("alert-table", "data"),
    Input("update-interval", "n_intervals"),
)
def update_alert_table(n_intervals):
    """Load last 50 anomaly_log rows across all tickers.
    Order by created_at DESC."""
    try:
        conn = _get_conn()
        df = pd.read_sql_query(
            """
            SELECT timestamp, ticker, zscore_score, if_score,
                   lstm_score, ensemble_score, is_flagged
            FROM anomaly_log
            ORDER BY created_at DESC
            LIMIT 50
            """,
            conn,
        )
        conn.close()

        # Round scores for display
        for col in ["zscore_score", "if_score", "lstm_score", "ensemble_score"]:
            if col in df.columns:
                df[col] = df[col].round(3)

        return df.to_dict("records")
    except Exception:
        return []

"""
dashboard/callbacks.py

All Dash callback functions for the Stock Anomaly Detector dashboard.
Callbacks read ONLY from the SQLite database — no model inference here.
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, State, html, ctx, no_update, dcc
from .pdf_generator import generate_anomaly_pdf

import sys
import os
import datetime

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

# ════════════════════════════════════════════════════════════════════
# Callback 5 — update_modal
# ════════════════════════════════════════════════════════════════════
@callback(
    Output("anomaly-modal-overlay", "className"),
    Output("modal-title", "children"),
    Output("modal-body", "children"),
    Input("alert-table", "active_cell"),
    Input("close-modal-btn", "n_clicks"),
    State("alert-table", "data"),
    prevent_initial_call=True,
)
def toggle_modal(active_cell, close_clicks, table_data):
    trigger = ctx.triggered_id
    
    if trigger == "close-modal-btn":
        return "cyber-modal-overlay hidden", no_update, no_update
        
    if trigger == "alert-table" and active_cell is not None:
        row_idx = active_cell["row"]
        if not table_data or row_idx >= len(table_data):
            return no_update, no_update, no_update
            
        row = table_data[row_idx]
        
        # Build explanation
        ticker = row.get("ticker", "Unknown")
        ts = row.get("timestamp", "Unknown")
        zscore = float(row.get("zscore_score", 0))
        iso_forest = float(row.get("if_score", 0))
        lstm = float(row.get("lstm_score", 0))
        ensemble = float(row.get("ensemble_score", 0))
        is_flagged = int(row.get("is_flagged", 0))
        
        title = f"LOG ENTRY DETAILED VIEW"
        
        is_test = "(TEST)" in ticker
        origin_text = "⚠️ SYNTHETIC INJECTION: Manually triggered by an Admin for system testing." if is_test else "🟢 NATURAL MARKET EVENT: Automatically detected from live telemetry."
        origin_color = "#f43f5e" if is_test else "#10b981"
        origin_bg = "rgba(244, 63, 94, 0.1)" if is_test else "rgba(16, 185, 129, 0.1)"
        
        body = [
            html.Div(f"Analysis for {ticker} at {ts}", style={"fontSize": "1.1rem", "marginBottom": "0.5rem", "color": "#F8FAFC"}),
            html.Div(
                origin_text, 
                style={
                    "padding": "10px", 
                    "backgroundColor": origin_bg, 
                    "color": origin_color, 
                    "borderLeft": f"3px solid {origin_color}",
                    "borderRadius": "4px",
                    "marginBottom": "1.5rem",
                    "fontSize": "0.85rem",
                    "fontWeight": "bold"
                }
            ),
            html.Div("MODEL BREAKDOWN:", style={"color": "#06b6d4", "fontFamily": "Fira Code", "marginBottom": "0.5rem"}),
        ]
        
        # Explanation strings
        z_exp = "Unusual statistical trading volume or price distribution detected." if zscore > 0.5 else "Statistical volatility remains within expected normal bounds."
        if_exp = "Clustering algorithms detected isolated out-of-bounds data points." if iso_forest > 0.5 else "Data points cluster normally with historical pricing."
        lstm_exp = "Neural Network failed to reconstruct the recent time-sequence, indicating a drastic pattern collapse." if lstm > 0.5 else "Recent sequence tracks perfectly with deep learning training memories."
        
        models = [
            ("Z-Score", zscore, z_exp),
            ("Isolation Forest", iso_forest, if_exp),
            ("LSTM Autoencoder", lstm, lstm_exp)
        ]
        
        for name, score, desc in models:
            score_color = "modal-danger" if score > 0.5 else "modal-highlight"
            body.append(
                html.Div(className="modal-score-item", children=[
                    html.Span(name, style={"fontWeight": "bold"}),
                    html.Span(f"{score:.3f} - ({'ANOMALOUS' if score > 0.5 else 'NORMAL'})", className=score_color)
                ])
            )
            body.append(html.Div(desc, style={"marginBottom": "1rem", "fontSize": "0.85rem", "paddingLeft": "0.5rem"}))
            
        summary_color = "modal-danger" if is_flagged else "modal-highlight"
        status_text = "System triggered an official anomaly alert because 2 or more models crossed the threshold." if is_flagged else "Consensus believes the market behavior is benign."
        
        body.append(html.Hr(style={"borderColor": "rgba(255,255,255,0.1)", "marginTop": "1.5rem", "marginBottom": "1rem"}))
        body.append(html.Div(className="modal-score-item", children=[
            html.Span("ENSEMBLE CONSENSUS:", style={"fontFamily": "Fira Code", "color": "#a1a1aa"}),
            html.Span(f"{ensemble:.3f} | {'FLAGGED' if is_flagged else 'NOT FLAGGED'}", className=summary_color)
        ]))
        body.append(html.Div(status_text, style={"fontSize": "0.95rem"}))
        
        return "cyber-modal-overlay", title, body
        
    return no_update, no_update, no_update

# ════════════════════════════════════════════════════════════════════
# Callback 6 — inject_anomaly
# ════════════════════════════════════════════════════════════════════
@callback(
    Output("injection-status", "children"),
    Input("inject-status-btn", "n_clicks"),
    State("ticker-dropdown", "value"),
    prevent_initial_call=True,
)
def inject_anomaly_into_ticker(n_clicks, ticker):
    if n_clicks is None or not ticker:
        return no_update
        
    flag_path = os.path.join(os.path.dirname(__file__), "..", f"inject_{ticker}.flag")
    with open(flag_path, "w") as f:
        f.write("trigger")
    return html.Div(
        f"🚨 SYNTHETIC CRASH ARMED FOR {ticker}! The models will flag it within 60 seconds.",
        className="toast-message"
    )
# ════════════════════════════════════════════════════════════════════
# Callback 7 — export_pdf
# ════════════════════════════════════════════════════════════════════
@callback(
    Output("download-pdf-component", "data"),
    Input("export-pdf-btn", "n_clicks"),
    State("alert-table", "data"),
    prevent_initial_call=True,
)
def export_anomaly_log_pdf(n_clicks, table_data):
    if not n_clicks or not table_data:
        return no_update
        
    df = pd.DataFrame(table_data)
    
    # We want to format columns properly
    df = df[["timestamp", "ticker", "zscore_score", "if_score", "lstm_score", "ensemble_score", "is_flagged"]]
    
    # Create temp file
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "tmp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    pdf_path = os.path.join(temp_dir, f"anomaly_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    generate_anomaly_pdf(df, pdf_path)
    
    return dcc.send_file(pdf_path)

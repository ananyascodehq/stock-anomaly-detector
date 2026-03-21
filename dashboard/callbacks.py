"""
dashboard/callbacks.py

All Dash callback functions for the Stock Anomaly Detector v2.
Callbacks read ONLY from the SQLite database -- no model inference here.
Spec: docs/design_instructions.md
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, html, ctx, no_update, dcc
from dashboard.app import app

from .pdf_generator import generate_anomaly_pdf

import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import Config

config = Config()

# -- Plotly theme constants (per design spec) --
PLOT_BG = "rgba(0,0,0,0)"
PAPER_BG = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255,255,255,0.04)"
FONT = dict(color="#9DA7B3", family="Inter, system-ui, sans-serif", size=11)
ACCENT = "#4A90E2"
DANGER = "#FF5A5F"
LOW = "#2ECC71"
MED = "#F5A623"


def _get_conn():
    db_path = os.path.join(os.path.dirname(__file__), "..", config.DB_PATH)
    return sqlite3.connect(db_path)


# ================================================================
# Ticker Tab Selection
# ================================================================
@app.callback(
    Output("selected-ticker", "data"),
    *[Output(f"ticker-tab-{t}", "className") for t in config.TICKERS],
    *[Input(f"ticker-tab-{t}", "n_clicks") for t in config.TICKERS],
    prevent_initial_call=True,
)
def select_ticker(*n_clicks_list):
    trigger = ctx.triggered_id
    selected = config.TICKERS[0]
    for t in config.TICKERS:
        if trigger == f"ticker-tab-{t}":
            selected = t
            break
    classes = ["ticker-btn active" if t == selected else "ticker-btn" for t in config.TICKERS]
    return (selected, *classes)


# ================================================================
# Page Title
# ================================================================
@app.callback(
    Output("page-title", "children"),
    Input("selected-ticker", "data"),
)
def update_page_title(ticker):
    return f"{ticker} Analysis"


# ================================================================
# Price Chart
# ================================================================
@app.callback(
    Output("price-chart", "figure"),
    Output("price-value", "children"),
    Output("price-delta", "children"),
    Output("price-delta", "className"),
    Input("update-interval", "n_intervals"),
    Input("selected-ticker", "data"),
)
def update_price_chart(n_intervals, ticker):
    fig = go.Figure()
    price_str = "--"
    delta_str = ""
    delta_class = "price-delta"

    try:
        conn = _get_conn()
        bars_df = pd.read_sql_query(
            "SELECT timestamp, close, volume FROM ohlcv WHERE ticker = ? ORDER BY timestamp DESC LIMIT 100",
            conn, params=(ticker,),
        )
        anomalies_df = pd.read_sql_query(
            "SELECT timestamp, ensemble_score FROM anomaly_log WHERE ticker = ? AND is_flagged = 1 ORDER BY timestamp DESC LIMIT 100",
            conn, params=(ticker,),
        )
        conn.close()

        if not bars_df.empty:
            bars_df = bars_df.sort_values("timestamp")
            latest_price = bars_df.iloc[-1]["close"]
            price_str = f"${latest_price:,.2f}"

            if len(bars_df) > 1:
                prev = bars_df.iloc[-2]["close"]
                if prev > 0:
                    pct = ((latest_price - prev) / prev) * 100
                    delta_str = f"{'+' if pct >= 0 else ''}{pct:.1f}% Volatility"
                    delta_class = "price-delta up" if pct >= 0 else "price-delta down"

            # Spline price line
            fig.add_trace(go.Scatter(
                x=bars_df["timestamp"], y=bars_df["close"],
                mode="lines", name="Close",
                line=dict(color=ACCENT, width=2, shape="spline", smoothing=1.0),
                hovertemplate="<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>",
            ))

            # Volume bars (low opacity)
            if "volume" in bars_df.columns:
                fig.add_trace(go.Bar(
                    x=bars_df["timestamp"], y=bars_df["volume"],
                    name="Volume", yaxis="y2",
                    marker_color="rgba(74,144,226,0.15)",
                    hoverinfo="skip",
                ))

        if not anomalies_df.empty:
            merged = anomalies_df.merge(bars_df, on="timestamp", how="inner")
            if not merged.empty:
                fig.add_trace(go.Scatter(
                    x=merged["timestamp"], y=merged["close"],
                    mode="markers", name="Anomaly",
                    marker=dict(color=DANGER, size=8, symbol="circle",
                                line=dict(width=1, color="rgba(255,90,95,0.5)")),
                    hovertemplate="<b>ANOMALY</b><br>%{x}<br>$%{y:.2f}<extra></extra>",
                ))

    except Exception:
        pass

    fig.update_layout(
        plot_bgcolor=PLOT_BG, paper_bgcolor=PAPER_BG, font=FONT,
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
                   showline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
                   showline=False, tickfont=dict(size=10)),
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    zeroline=False, showticklabels=False, range=[0, None]),
        margin=dict(l=40, r=20, t=10, b=30),
        legend=dict(font=dict(color="#E6EDF3", size=11), orientation="h",
                    yanchor="top", y=1.02, xanchor="left", x=0),
        showlegend=False,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1E2530",
            bordercolor="rgba(255,255,255,0.1)",
            font=dict(color="#E6EDF3", family="Inter, system-ui, sans-serif", size=12),
        ),
    )
    return fig, price_str, delta_str, delta_class


# ================================================================
# Ensemble Score Gauge + Context
# ================================================================
@app.callback(
    Output("score-gauge", "figure"),
    Output("ensemble-score-display", "children"),
    Output("ensemble-score-display", "className"),
    Output("ensemble-delta-display", "children"),
    Output("ensemble-delta-display", "className"),
    Output("ensemble-status-label", "children"),
    Output("ensemble-status-label", "className"),
    Output("ensemble-context", "children"),
    Input("update-interval", "n_intervals"),
    Input("selected-ticker", "data"),
)
def update_ensemble(n_intervals, ticker):
    score = 0.0
    prev_score = 0.0
    last_anomaly_ago = "N/A"
    models_triggered = 0

    try:
        conn = _get_conn()
        rows = pd.read_sql_query(
            "SELECT ensemble_score, zscore_score, if_score, lstm_score, created_at FROM anomaly_log WHERE ticker = ? ORDER BY created_at DESC LIMIT 2",
            conn, params=(ticker,),
        )
        # Last anomaly time
        last_flag = pd.read_sql_query(
            "SELECT created_at FROM anomaly_log WHERE ticker = ? AND is_flagged = 1 ORDER BY created_at DESC LIMIT 1",
            conn, params=(ticker,),
        )
        conn.close()

        if not rows.empty:
            score = float(rows.iloc[0]["ensemble_score"])
            z = float(rows.iloc[0]["zscore_score"])
            i = float(rows.iloc[0]["if_score"])
            l = float(rows.iloc[0]["lstm_score"])
            models_triggered = sum(1 for threshold, s in [(0.5, z), (0.6, i), (0.5, l)] if s > threshold)
            if len(rows) > 1:
                prev_score = float(rows.iloc[1]["ensemble_score"])

        if not last_flag.empty:
            try:
                last_t = pd.to_datetime(last_flag.iloc[0]["created_at"])
                diff = (datetime.datetime.now() - last_t).total_seconds() / 60
                last_anomaly_ago = f"{int(diff)} min ago"
            except Exception:
                last_anomaly_ago = "recently"

    except Exception:
        pass

    # Gauge figure (thin arc)
    bar_color = LOW if score < 0.4 else (MED if score < 0.5 else DANGER)

    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=score,
        gauge=dict(
            axis=dict(range=[0, 1], tickcolor="#9DA7B3", dtick=0.25,
                      tickfont=dict(size=9, color="#9DA7B3")),
            bar=dict(color=bar_color, thickness=0.6),
            bgcolor="rgba(255,255,255,0.02)",
            bordercolor="rgba(255,255,255,0.05)",
            borderwidth=1,
            threshold=dict(line=dict(color="#9DA7B3", width=1), thickness=0.8, value=0.5),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=PLOT_BG, font=FONT,
        margin=dict(l=20, r=20, t=20, b=0),
        height=160,
    )

    # Score display
    score_text = f"{score:.2f}"
    if score > 0.5:
        score_class = "ensemble-score-value high"
    elif score > 0.4:
        score_class = "ensemble-score-value moderate"
    else:
        score_class = "ensemble-score-value normal"

    # Delta
    delta = score - prev_score
    if delta >= 0:
        delta_text = f"+{delta:.2f}"
        delta_class = "ensemble-delta up"
    else:
        delta_text = f"{delta:.2f}"
        delta_class = "ensemble-delta down"

    # Status label
    if score > 0.5:
        status_text = "High Anomaly Detected"
        status_class = "ensemble-status-label high"
    elif score > 0.4:
        status_text = "Moderate Activity"
        status_class = "ensemble-status-label moderate"
    else:
        status_text = "Normal Behavior"
        status_class = "ensemble-status-label normal"

    # Context
    context_text = f"Last anomaly: {last_anomaly_ago} | Model status: {models_triggered}/3 triggered"

    return fig, score_text, score_class, delta_text, delta_class, status_text, status_class, context_text


# ================================================================
# Model Distribution (HTML bars rendered via callback)
# ================================================================
@app.callback(
    Output("model-bars-container", "children"),
    Output("model-agreement", "children"),
    Output("model-agreement", "className"),
    Input("update-interval", "n_intervals"),
    Input("selected-ticker", "data"),
)
def update_model_distribution(n_intervals, ticker):
    scores = {"Z-Score": 0.0, "Isolation Forest": 0.0, "LSTM Autoencoder": 0.0}

    try:
        conn = _get_conn()
        row = pd.read_sql_query(
            "SELECT zscore_score, if_score, lstm_score FROM anomaly_log WHERE ticker = ? ORDER BY created_at DESC LIMIT 1",
            conn, params=(ticker,),
        )
        conn.close()
        if not row.empty:
            scores["Z-Score"] = float(row.iloc[0]["zscore_score"])
            scores["Isolation Forest"] = float(row.iloc[0]["if_score"])
            scores["LSTM Autoencoder"] = float(row.iloc[0]["lstm_score"])
    except Exception:
        pass

    above_count = sum(1 for v in scores.values() if v > 0.5)
    if above_count > 0:
        agreement_text = f"{above_count} of 3 models indicate anomaly"
        agreement_class = "model-agreement"
    else:
        agreement_text = "0 of 3 models indicate anomaly"
        agreement_class = "model-agreement normal"

    bars = []
    for name, val in scores.items():
        threshold = 0.6 if name == "Isolation Forest" else 0.5
        is_above = val > threshold
        dot_class = "model-dot above" if is_above else "model-dot below"
        fill_class = "model-bar-fill above" if is_above else "model-bar-fill below"
        label_extra = html.Span(" (Above Threshold)", className="model-item-label") if is_above else ""

        bars.append(
            html.Div(className="model-item", children=[
                html.Div(className="model-item-header", children=[
                    html.Div(className="model-item-name", children=[
                        html.Span(className=dot_class),
                        html.Span(name),
                    ]),
                    html.Div(children=[
                        html.Span(f"{val:.2f}", className="model-item-score"),
                        label_extra,
                    ]),
                ]),
                html.Div(className="model-bar-track", children=[
                    html.Div(className=fill_class, style={"width": f"{val * 100}%"}),
                    html.Div(className="model-bar-threshold", style={"left": f"{threshold * 100}%"}),
                ]),
            ])
        )

    return bars, agreement_text, agreement_class


# ================================================================
# Anomaly History Table
# ================================================================
@app.callback(
    Output("alert-table", "data"),
    Input("update-interval", "n_intervals"),
    Input("flagged-toggle", "value"),
)
def update_alert_table(n_intervals, flagged_toggle):
    try:
        conn = _get_conn()
        df = pd.read_sql_query(
            "SELECT timestamp, ticker, zscore_score, if_score, lstm_score, ensemble_score, is_flagged FROM anomaly_log ORDER BY created_at DESC LIMIT 50",
            conn,
        )
        conn.close()

        for col in ["zscore_score", "if_score", "lstm_score", "ensemble_score"]:
            if col in df.columns:
                df[col] = df[col].round(3)

        # Compute severity
        def get_severity(es):
            if es > 0.5: return "HIGH"
            if es >= 0.4: return "MEDIUM"
            return "LOW"

        df["severity"] = df["ensemble_score"].apply(get_severity)
        df["status"] = df["is_flagged"].apply(lambda x: "FLAGGED" if x == 1 else "NORMAL")

        if flagged_toggle and "flagged" in flagged_toggle:
            df = df[df["is_flagged"] == 1]

        return df[["timestamp", "ticker", "severity", "ensemble_score", "status"]].to_dict("records")
    except Exception:
        return []


# ================================================================
# Modal
# ================================================================
@app.callback(
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
        return "modal-overlay hidden", no_update, no_update

    if trigger == "alert-table" and active_cell is not None:
        row_idx = active_cell["row"]
        if not table_data or row_idx >= len(table_data):
            return no_update, no_update, no_update

        row = table_data[row_idx]
        ticker = row.get("ticker", "Unknown")
        ts = row.get("timestamp", "Unknown")
        ensemble = float(row.get("ensemble_score", 0))
        severity = row.get("severity", "LOW")
        status = row.get("status", "NORMAL")

        # Fetch full scores for this entry
        zscore = 0.0
        iso_forest = 0.0
        lstm = 0.0
        try:
            conn = _get_conn()
            detail = pd.read_sql_query(
                "SELECT zscore_score, if_score, lstm_score FROM anomaly_log WHERE timestamp = ? AND ticker = ? LIMIT 1",
                conn, params=(ts, ticker),
            )
            conn.close()
            if not detail.empty:
                zscore = float(detail.iloc[0]["zscore_score"])
                iso_forest = float(detail.iloc[0]["if_score"])
                lstm = float(detail.iloc[0]["lstm_score"])
        except Exception:
            pass

        title = f"LOG ENTRY DETAIL"

        # Build explanation
        reasons = []
        if zscore > 0.5:
            reasons.append("volume spike")
        if iso_forest > 0.5:
            reasons.append("clustering outlier")
        if lstm > 0.5:
            reasons.append("sequence pattern collapse")
        explanation = "Detected due to " + " + ".join(reasons) if reasons else "No anomalous signals detected"

        body = [
            html.Div(f"Analysis for {ticker} at {ts}", style={"fontSize": "14px", "marginBottom": "12px", "color": "#E6EDF3", "fontWeight": "600"}),
            html.Div(explanation, style={"padding": "10px 12px", "backgroundColor": "rgba(255,90,95,0.06)" if reasons else "rgba(46,204,113,0.06)", "color": DANGER if reasons else LOW, "borderLeft": f"3px solid {DANGER if reasons else LOW}", "borderRadius": "4px", "marginBottom": "16px", "fontSize": "13px"}),
            html.Div("MODEL SCORES:", style={"color": "#9DA7B3", "fontWeight": "600", "fontSize": "11px", "letterSpacing": "0.08em", "marginBottom": "8px"}),
        ]

        models = [("Z-Score", zscore, 0.5), ("Isolation Forest", iso_forest, 0.6), ("LSTM Autoencoder", lstm, 0.5)]
        for name, s, t in models:
            score_class = "modal-danger" if s > t else "modal-highlight"
            label = "Above Threshold" if s > t else "Normal"
            body.append(html.Div(className="modal-score-item", children=[
                html.Span(name, style={"fontWeight": "500"}),
                html.Span(f"{s:.3f} - {label}", className=score_class),
            ]))

        body.append(html.Hr(style={"borderColor": "rgba(255,255,255,0.05)", "margin": "16px 0"}))
        summary_class = "modal-danger" if status == "FLAGGED" else "modal-highlight"
        body.append(html.Div(className="modal-score-item", children=[
            html.Span("ENSEMBLE:", style={"color": "#9DA7B3", "fontWeight": "600"}),
            html.Span(f"{ensemble:.3f} | {status}", className=summary_class),
        ]))

        return "modal-overlay", title, body

    return no_update, no_update, no_update


# ================================================================
# Inject Anomaly
# ================================================================
@app.callback(
    Output("injection-status", "children"),
    Input("inject-status-btn", "n_clicks"),
    State("selected-ticker", "data"),
    prevent_initial_call=True,
)
def inject_anomaly_into_ticker(n_clicks, ticker):
    if n_clicks is None or not ticker:
        return no_update

    flag_path = os.path.join(os.path.dirname(__file__), "..", f"inject_{ticker}.flag")
    with open(flag_path, "w") as f:
        f.write("trigger")
    return html.Div(
        f"Synthetic crash armed for {ticker}. Detection within 60s.",
        className="toast-message",
    )


# ================================================================
# Export PDF
# ================================================================
@app.callback(
    Output("download-pdf-component", "data"),
    Input("export-pdf-btn", "n_clicks"),
    State("alert-table", "data"),
    prevent_initial_call=True,
)
def export_anomaly_log_pdf(n_clicks, table_data):
    if not n_clicks or not table_data:
        return no_update

    # Fetch full data for PDF (not the filtered table columns)
    try:
        conn = _get_conn()
        df = pd.read_sql_query(
            "SELECT timestamp, ticker, zscore_score, if_score, lstm_score, ensemble_score, is_flagged FROM anomaly_log ORDER BY created_at DESC LIMIT 50",
            conn,
        )
        conn.close()
    except Exception:
        df = pd.DataFrame(table_data)

    temp_dir = os.path.join(os.path.dirname(__file__), "..", "tmp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    pdf_path = os.path.join(temp_dir, f"anomaly_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    generate_anomaly_pdf(df, pdf_path)
    return dcc.send_file(pdf_path)


# ================================================================
# Tooltip Toggle
# ================================================================
@app.callback(
    Output("chart-info-tooltip", "style"),
    Input("chart-info-icon", "n_clicks"),
    State("chart-info-tooltip", "style"),
    prevent_initial_call=False,
)
def toggle_info_tooltip(n_clicks, current_style):
    if not current_style:
        current_style = {}
    
    new_style = current_style.copy()
    
    if n_clicks and n_clicks > 0:
        if current_style.get("display") == "none":
            new_style["display"] = "block"
        else:
            new_style["display"] = "none"
    else:
        new_style["display"] = "none"
        
    return new_style


# ================================================================
# View Toggle (Dashboard vs Support)
# ================================================================
@app.callback(
    Output("dashboard-view", "style"),
    Output("support-view", "style"),
    Output("nav-dashboard-btn", "className"),
    Output("nav-support-btn", "className"),
    Input("nav-dashboard-btn", "n_clicks"),
    Input("nav-support-btn", "n_clicks"),
    prevent_initial_call=False,
)
def switch_views(dash_clicks, supp_clicks):
    trigger = ctx.triggered_id
    
    dash_style = {"display": "flex", "flexDirection": "column", "gap": "24px"}
    supp_style = {"display": "none", "flexDirection": "column", "gap": "24px"}
    # The default sidebar classes
    dash_class = "sidebar-nav-item active"
    supp_class = "sidebar-support"
    
    if trigger == "nav-support-btn":
        dash_style["display"] = "none"
        supp_style["display"] = "flex"
        dash_class = "sidebar-nav-item"
        supp_class = "sidebar-support active"
        
    return dash_style, supp_style, dash_class, supp_class

"""
dashboard/layout.py

All Dash layout definitions for the Stock Anomaly Detector dashboard.
Panels: Price Chart, Anomaly Score Gauge, Model Comparison Bar,
        Alert Log Table, Ticker Dropdown, Update Interval.
"""

from dash import html, dcc, dash_table
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import Config

config = Config()


def create_layout(app):
    return html.Div(
        className="app-wrapper",
        children=[
            # ── Header ──────────────────────────────────────────────
            html.Header(
                className="dashboard-header",
                children=[
                    html.H1("STOCK_ANOMALY_DETECTOR", className="dashboard-title"),
                    html.Div(
                        className="system-status",
                        children=[
                            html.Span(className="indicator"),
                            html.Span("SYSTEM: ONLINE"),
                        ],
                    ),
                ],
            ),
            # ── Main Container ──────────────────────────────────────
            html.Main(
                className="dashboard-container",
                children=[
                    # Controls row: Ticker dropdown
                    html.Div(
                        className="controls-row",
                        children=[
                            html.Label(
                                "> SELECT_TICKER",
                                className="control-label",
                            ),
                            dcc.Dropdown(
                                id="ticker-dropdown",
                                options=[
                                    {"label": t, "value": t}
                                    for t in config.TICKERS
                                ],
                                value=config.TICKERS[0],
                                clearable=False,
                                className="cyber-dropdown",
                            ),
                            html.Div(
                                className="injector-container",
                                children=[
                                    html.Button(
                                        "INJECT SYNTHETIC ANOMALY",
                                        id="inject-status-btn",
                                        className="cyber-btn-inject"
                                    ),
                                    html.Span(
                                        "[TEST PURPOSES ONLY - NOT REAL DATA]",
                                        className="injector-disclaimer"
                                    )
                                ]
                            ),
                            html.Div(id="injection-status")
                        ],
                    ),
                    # KPI row: Gauge + Model Comparison side by side
                    html.Div(
                        className="kpi-grid",
                        children=[
                            # Anomaly Score Gauge
                            html.Div(
                                className="kpi-card gauge-card",
                                children=[
                                    html.Div(
                                        "ENSEMBLE_SCORE", className="kpi-title"
                                    ),
                                    html.Div(
                                        "A weighted consensus of all 3 AI models. A score over 0.5 triggers an official system alert.",
                                        style={"fontSize": "0.75rem", "color": "#a1a1aa", "marginBottom": "5px", "textAlign": "center", "fontFamily": "Inter, sans-serif"}
                                    ),
                                    dcc.Graph(
                                        id="score-gauge",
                                        config={"displayModeBar": False},
                                        style={"height": "200px"},
                                    ),
                                ],
                            ),
                            # Model Comparison Bar Chart
                            html.Div(
                                className="kpi-card",
                                children=[
                                    html.Div(
                                        "MODEL_COMPARISON", className="kpi-title"
                                    ),
                                    html.Div(
                                        "Real-time reading of precisely which individual model is detecting abnormal market behavior.",
                                        style={"fontSize": "0.75rem", "color": "#a1a1aa", "marginBottom": "5px", "textAlign": "center", "fontFamily": "Inter, sans-serif"}
                                    ),
                                    dcc.Graph(
                                        id="model-comparison",
                                        config={"displayModeBar": False},
                                        style={"height": "200px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Main Price Chart
                    html.Div(
                        className="chart-container-wrapper",
                        children=[
                            html.Div(
                                className="chart-header",
                                children=[
                                    html.H2(
                                        "Price + Anomaly Overlay",
                                        className="chart-title",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="chart-body",
                                children=[
                                    dcc.Graph(
                                        id="price-chart",
                                        style={
                                            "height": "100%",
                                            "width": "100%",
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Alert Log Table
                    html.Div(
                        className="chart-container-wrapper",
                        children=[
                            html.Div(
                                className="chart-header",
                                children=[
                                    html.H2(
                                        "Alert Log",
                                        className="chart-title",
                                    ),
                                ],
                            ),
                            dash_table.DataTable(
                                id="alert-table",
                                columns=[
                                    {"name": "Timestamp", "id": "timestamp"},
                                    {"name": "Ticker", "id": "ticker"},
                                    {"name": "Z-Score", "id": "zscore_score"},
                                    {"name": "Iso Forest", "id": "if_score"},
                                    {"name": "LSTM", "id": "lstm_score"},
                                    {"name": "Ensemble", "id": "ensemble_score"},
                                    {"name": "Flagged", "id": "is_flagged"},
                                ],
                                style_table={
                                    "overflowX": "auto",
                                    "overflowY": "auto",
                                    "height": "400px",
                                    "borderRadius": "4px",
                                },
                                fixed_rows={"headers": True},
                                style_header={
                                    "backgroundColor": "rgba(24, 24, 27, 0.95)",
                                    "color": "#06b6d4",
                                    "fontFamily": "Fira Code, monospace",
                                    "fontSize": "0.8rem",
                                    "fontWeight": "600",
                                    "border": "none",
                                    "borderBottom": "1px solid rgba(255, 255, 255, 0.1)",
                                    "textTransform": "uppercase",
                                },
                                style_cell={
                                    "backgroundColor": "transparent",
                                    "color": "#a1a1aa",
                                    "fontFamily": "Inter, sans-serif",
                                    "fontSize": "0.85rem",
                                    "border": "none",
                                    "borderBottom": "1px solid rgba(255, 255, 255, 0.05)",
                                    "padding": "10px 14px",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {
                                            "filter_query": "{is_flagged} = 1",
                                        },
                                        "color": "#f43f5e",
                                        "fontWeight": "bold",
                                    }
                                ],
                                css=[
                                    {
                                        "selector": "tr:hover",
                                        "rule": "background-color: transparent !important;"
                                    },
                                    {
                                        "selector": "tr:hover td",
                                        "rule": "background-color: rgba(6, 182, 212, 0.1) !important; color: #06b6d4 !important;"
                                    },
                                    {
                                        "selector": "td.focused",
                                        "rule": "background-color: rgba(6, 182, 212, 0.15) !important; outline: 1px solid #06b6d4 !important; box-shadow: none !important;"
                                    },
                                    {
                                        "selector": ".dash-spreadsheet-container .dash-spreadsheet-inner *",
                                        "rule": "outline: none !important;"
                                    }
                                ],
                                page_action="none",
                            ),
                        ],
                    ),
                    # User Guide / Operations Manual
                    html.Div(
                        className="guide-container",
                        children=[
                            html.Details(
                                className="guide-details",
                                children=[
                                    html.Summary(
                                        "USER_GUIDE & OPERATIONS_MANUAL",
                                        className="guide-summary",
                                    ),
                                    html.Div(
                                        className="guide-content",
                                        children=[
                                            # Item 1: Pipeline
                                            html.Div(
                                                className="guide-item",
                                                children=[
                                                    html.Div("01 // HOW IT WORKS (THE PIPELINE)", className="guide-item-title"),
                                                    html.Div(
                                                        "Every minute, this system collects real-time stock price and volume data using Yahoo Finance. "
                                                        "It then calculates 'features'—which are statistical clues like how fast the price is moving compared to normal. "
                                                        "These clues are fed into our AI models to hunt for unusual market behaviors.",
                                                        className="guide-item-text"
                                                    ),
                                                ]
                                            ),
                                            # Item 2: Ensemble
                                            html.Div(
                                                className="guide-item",
                                                children=[
                                                    html.Div("02 // AI ENSEMBLE LOGIC", className="guide-item-title"),
                                                    html.Div(
                                                        "We don't trust just one model! We use three different approaches: a Statistical test (Z-Score), "
                                                        "an AI that looks for isolated unusual patterns (Isolation Forest), and a deep learning Neural Network analyzing time sequences (LSTM). "
                                                        "To prevent false alarms, at least 2 out of our 3 models must mathematically agree to officially flag an anomaly.",
                                                        className="guide-item-text"
                                                    ),
                                                ]
                                            ),
                                            # Item 3: Monitoring
                                            html.Div(
                                                className="guide-item",
                                                children=[
                                                    html.Div("03 // HOW TO READ THE DASHBOARD", className="guide-item-title"),
                                                    html.Div(
                                                        "Use the 'SELECT TICKER' dropdown to focus on a specific stock. The big gauge shows the combined 'Ensemble Score' from 0 (Normal) to 1 (Extreme Anomaly). "
                                                        "If the needle crosses into the right side (above 0.5), it means the models have detected a highly unusual, coordinated market event!",
                                                        className="guide-item-text"
                                                    ),
                                                ]
                                            ),
                                            # Item 4: Disclaimer
                                            html.Div(
                                                className="guide-item",
                                                children=[
                                                    html.Div("04 // LEGAL DISCLAIMER", className="guide-item-title"),
                                                    html.Div(
                                                        "This is a statistical research tool designed to flag math abnormalities, not provide financial or trading advice. "
                                                        "Always do your own research before making financial decisions. Users assume all trading risks.",
                                                        className="guide-item-text text-danger"
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Hidden Interval component for polling
                    dcc.Interval(
                        id="update-interval",
                        interval=config.DASH_UPDATE_INTERVAL_MS,
                        n_intervals=0,
                    ),
                ],
            ),
            # ── Modal Container ──────────────────────────────────────
            html.Div(
                id="anomaly-modal-overlay",
                className="cyber-modal-overlay hidden",
                children=[
                    html.Div(
                        className="cyber-modal-content",
                        children=[
                            html.Div(
                                className="cyber-modal-header",
                                children=[
                                    html.H3("ANOMALY LOG EXPLANATION", className="chart-title", id="modal-title"),
                                    html.Button("✕", id="close-modal-btn", className="cyber-btn-close"),
                                ]
                            ),
                            html.Div(id="modal-body", className="cyber-modal-body")
                        ]
                    )
                ]
            ),
        ],
    )

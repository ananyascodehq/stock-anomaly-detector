"""
dashboard/layout.py

Dash layout for the Stock Anomaly Detector v2.
Implements: Sidebar, Top Bar, Price Chart, Ensemble Gauge,
            Model Distribution, Anomaly History Table.
Spec: docs/design_instructions.md
"""

from dash import html, dcc, dash_table
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import Config

config = Config()


def create_layout(app):
    return html.Div(
        className="app-shell",
        children=[
            # ── Top Bar ──────────────────────────────────────
            html.Header(
                className="topbar",
                children=[
                    html.Div(
                        className="topbar-left",
                        children=[
                            html.Span(
                                "STOCK ANOMALY DETECTOR",
                                className="topbar-brand",
                            ),
                            html.Div(
                                className="topbar-tickers",
                                id="ticker-tabs",
                                children=[
                                    html.Button(
                                        t,
                                        id=f"ticker-tab-{t}",
                                        className="ticker-btn active" if i == 0 else "ticker-btn",
                                        n_clicks=0,
                                    )
                                    for i, t in enumerate(config.TICKERS)
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            # Hidden store for selected ticker
            dcc.Store(id="selected-ticker", data=config.TICKERS[0]),

            # ── Sidebar ──────────────────────────────────────
            html.Nav(
                className="sidebar",
                children=[
                    html.Div(
                        className="sidebar-logo",
                        children=[
                            html.Div("Quantified Exec", className="sidebar-logo-title"),
                            html.Div("PRECISION TERMINAL", className="sidebar-logo-sub"),
                        ],
                    ),
                    html.Div(
                        className="sidebar-nav",
                        children=[
                            html.Div(
                                className="sidebar-nav-item active",
                                id="nav-dashboard-btn",
                                n_clicks=0,
                                style={"cursor": "pointer"},
                                children=[
                                    html.Div(className="sidebar-nav-icon", children=[
                                        html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%239DA7B3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='7' height='7'/%3E%3Crect x='14' y='3' width='7' height='7'/%3E%3Crect x='3' y='14' width='7' height='7'/%3E%3Crect x='14' y='14' width='7' height='7'/%3E%3C/svg%3E", style={"width": "18px", "height": "18px"}),
                                    ]),
                                    html.Span("Dashboard"),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="sidebar-bottom",
                        children=[
                            html.Button(
                                "Simulate Anomaly",
                                id="inject-status-btn",
                                className="sidebar-inject-btn",
                                title="Inject synthetic anomaly to test detection system",
                                n_clicks=0,
                            ),
                            html.Div(id="injection-status"),
                            html.Div(
                                className="sidebar-support",
                                id="nav-support-btn",
                                n_clicks=0,
                                style={"cursor": "pointer"},
                                children=[
                                    html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%239DA7B3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'%3E%3C/path%3E%3Cline x1='12' y1='17' x2='12.01' y2='17'%3E%3C/line%3E%3C/svg%3E", style={"marginRight": "4px"}),
                                    html.Span("Support"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),

            # ── Main Content ─────────────────────────────────
            html.Main(
                className="main-content",
                children=[
                    html.Div(id="dashboard-view", style={"display": "flex", "flexDirection": "column", "gap": "24px"}, children=[
                    # Page Header
                    html.Div(
                        className="page-header",
                        children=[
                            html.Div(
                                className="page-header-left",
                                children=[
                                    html.H1(
                                        id="page-title",
                                        className="page-header-title",
                                    ),
                                    html.Div(
                                        className="page-header-subtitle",
                                        children=[
                                            html.Span(className="live-dot"),
                                            html.Span("Live processing"),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                className="page-header-right",
                                children=[
                                    html.Div(
                                        className="sensitivity-control",
                                        children=[
                                            html.Span("SENSITIVITY THRESHOLD:", className="sensitivity-label"),
                                            dcc.Slider(
                                                id="sensitivity-slider", min=0.1, max=0.9, step=0.01, value=0.5,
                                                marks=None,
                                                tooltip={"placement": "bottom", "always_visible": False}
                                            ),
                                            html.Span(id="detected-count-container", className="sensitivity-hint"),
                                        ],
                                    ),
                                    html.Button(
                                        "EXPORT PDF",
                                        id="export-pdf-btn",
                                        className="btn-export",
                                        n_clicks=0,
                                    ),
                                    dcc.Download(id="download-pdf-component"),
                                ],
                            ),
                        ],
                    ),

                    # Chart Row: Price Chart + Ensemble Score
                    html.Div(
                        className="chart-row",
                        children=[
                            # Price Chart
                            html.Div(
                                className="card price-card",
                                children=[
                                    html.Div(
                                        className="price-card-header",
                                        children=[
                                            html.Div(
                                                children=[
                                                    html.Div(
                                                        className="card-title-with-info",
                                                        children=[
                                                            html.Div("LIVE PRICE TRACKING", className="card-title", style={"marginBottom": "0"}),
                                                            html.Div(
                                                                className="info-icon-wrapper",
                                                                id="chart-info-icon",
                                                                n_clicks=0,
                                                                children=[
                                                                    html.Img(
                                                                        src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%239DA7B3' stroke-width='2'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='12' y1='16' x2='12' y2='12'/%3E%3Cline x1='12' y1='8' x2='12.01' y2='8'/%3E%3C/svg%3E",
                                                                        className="info-icon",
                                                                    ),
                                                                    html.Div(
                                                                        className="info-tooltip",
                                                                        id="chart-info-tooltip",
                                                                        style={"display": "none"},
                                                                        children=[
                                                                            html.Div("What does this chart show?", style={"fontWeight": "600", "marginBottom": "6px", "color": "#E6EDF3"}),
                                                                            html.Div(
                                                                                "This chart tracks the real-time price movement of the selected stock ticker. "
                                                                                "The blue line shows the closing price over time. Red dots mark moments where "
                                                                                "our AI models detected unusual market behavior (anomalies). "
                                                                                "A sudden spike or dip combined with red markers means the system flagged "
                                                                                "a potential flash crash, volume surge, or irregular pattern.",
                                                                                style={"lineHeight": "1.6"},
                                                                            ),
                                                                        ],
                                                                    ),
                                                                ],
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        className="price-card-info",
                                                        children=[
                                                            html.Span(id="price-value", className="price-value"),
                                                            html.Span(id="price-delta", className="price-delta"),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="price-card-controls",
                                                children=[
                                                    html.Span("LIVE", className="live-badge"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="price-chart-body",
                                        children=[
                                            dcc.Graph(
                                                id="price-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "100%", "width": "100%"},
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            # Ensemble Score
                            html.Div(
                                className="card ensemble-card",
                                children=[
                                    html.Div("ENSEMBLE ANOMALY SCORE", className="card-title"),
                                    html.Div(
                                        className="ensemble-gauge-wrapper",
                                        children=[
                                            dcc.Graph(
                                                id="score-gauge",
                                                config={"displayModeBar": False},
                                                style={"height": "160px"},
                                            ),
                                        ],
                                    ),
                                    html.Div(id="ensemble-score-display", className="ensemble-score-value"),
                                    html.Div(id="ensemble-delta-display", className="ensemble-delta"),
                                    html.Div(id="ensemble-status-label", className="ensemble-status-label"),
                                    html.Div(id="ensemble-context", className="ensemble-context"),
                                    html.Div("Severity Logic: >0.5 HIGH, >0.4 MED", style={"fontSize": "10px", "color": "gray", "textAlign": "center"}),
                                    dcc.Graph(id="anomaly-sparkline", config={"displayModeBar": False}, style={"height": "50px", "marginTop": "10px"}),
                                ],
                            ),
                        ],
                    ),

                    # Bottom Row: Model Distribution + Table
                    html.Div(
                        className="bottom-row",
                        children=[
                            # Model Distribution
                            html.Div(
                                className="card model-dist-card",
                                children=[
                                    html.Div("MODEL DISTRIBUTION", className="card-title"),
                                    html.Div(id="model-agreement", className="model-agreement"),
                                    html.Div(id="model-bars-container"),
                                ],
                            ),
                            # Anomaly History Table
                            html.Div(
                                className="card history-card",
                                children=[
                                    html.Div(
                                        className="card-title-row",
                                        children=[
                                            html.Div("ANOMALY HISTORY LOG", className="card-title"),
                                            html.Div(
                                                className="history-controls",
                                                children=[
                                                    html.Span("Show flagged only", className="toggle-label"),
                                                    dcc.Checklist(
                                                        id="flagged-toggle",
                                                        options=[{"label": "", "value": "flagged"}],
                                                        value=[],
                                                        inline=True,
                                                    ),

                                                ],
                                            ),
                                        ],
                                    ),
                                    dash_table.DataTable(
                                        id="alert-table",
                                        columns=[
                                            {"name": "TIMESTAMP", "id": "timestamp"},
                                            {"name": "TICKER", "id": "ticker"},
                                            {"name": "SEVERITY", "id": "severity"},
                                            {"name": "ENSEMBLE", "id": "ensemble_score"},
                                            {"name": "STATUS", "id": "status"},
                                        ],
                                        style_table={
                                            "overflowX": "auto",
                                            "overflowY": "auto",
                                            "maxHeight": "320px",
                                        },
                                        fixed_rows={"headers": True},
                                        style_header={
                                            "backgroundColor": "#11161D",
                                            "color": "#9DA7B3",
                                            "fontFamily": "Inter, system-ui, sans-serif",
                                            "fontSize": "11px",
                                            "fontWeight": "600",
                                            "border": "none",
                                            "borderBottom": "1px solid rgba(255,255,255,0.05)",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "0.08em",
                                            "padding": "10px 12px",
                                        },
                                        style_cell={
                                            "backgroundColor": "transparent",
                                            "color": "#E6EDF3",
                                            "fontFamily": "Inter, system-ui, sans-serif",
                                            "fontSize": "13px",
                                            "border": "none",
                                            "borderBottom": "1px solid rgba(255,255,255,0.03)",
                                            "padding": "10px 12px",
                                        },
                                        style_data_conditional=[
                                            {
                                                "if": {"filter_query": "{severity} = 'HIGH'"},
                                                "backgroundColor": "rgba(255,90,95,0.06)",
                                            },
                                            {
                                                "if": {"filter_query": "{severity} = 'MEDIUM'"},
                                                "backgroundColor": "rgba(245,166,35,0.06)",
                                            },
                                            {
                                                "if": {"filter_query": "{status} = 'FLAGGED'"},
                                                "color": "#FF5A5F",
                                                "fontWeight": "600",
                                            },
                                        ],
                                        css=[
                                            {"selector": "td.focused", "rule": "background-color: rgba(74,144,226,0.08) !important; outline: none !important;"},
                                            {"selector": ".dash-spreadsheet-container .dash-spreadsheet-inner *", "rule": "outline: none !important;"},
                                        ],
                                        page_action="none",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ]),
                    
                    html.Div(id="support-view", style={"display": "none", "flexDirection": "column", "gap": "60px", "paddingTop": "20px"}, children=[
                        
                        # Section 1: The Science of Detection
                        html.Div(className="support-section", children=[
                            html.Div(className="support-section-header", children=[
                                html.H2("The Science of Detection", className="support-h2"),
                                html.P("Our ensemble approach combines classical statistical methods with state-of-the-art deep learning. Operating on standard 1-minute (1m) intervals via Yahoo Finance data.", className="support-subtitle")
                            ]),
                            html.Div(className="support-grid-3", children=[
                                html.Div(className="support-card", children=[
                                    html.Div(className="support-card-header", children=[
                                        html.Div(className="support-card-icon", children=[
                                            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234A90E2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='22 12 18 12 15 21 9 3 6 12 2 12'%3E%3C/polyline%3E%3C/svg%3E")
                                        ]),
                                        html.H4("Z-Score Analysis")
                                    ]),
                                    html.P("Calculates standard deviations from the mean moving average. Best for detecting immediate price flash-crashes and sudden volume explosions.", className="support-card-text")
                                ]),
                                html.Div(className="support-card", children=[
                                    html.Div(className="support-card-header", children=[
                                        html.Div(className="support-card-icon", children=[
                                            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234A90E2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolygon points='12 2 20 12 16 12 22 22 2 22 8 12 4 12 12 2'%3E%3C/polygon%3E%3C/svg%3E")
                                        ]),
                                        html.H4("Isolation Forest")
                                    ]),
                                    html.P("A non-parametric algorithm that isolates observations by randomly selecting a feature and then randomly selecting a split value between max and min values.", className="support-card-text")
                                ]),
                                html.Div(className="support-card", children=[
                                    html.Div(className="support-card-header", children=[
                                        html.Div(className="support-card-icon", children=[
                                            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234A90E2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'%3E%3C/path%3E%3C/svg%3E")
                                        ]),
                                        html.H4("LSTM Autoencoder")
                                    ]),
                                    html.P("Long Short-Term Memory neural networks trained to reconstruct 'normal' data. High reconstruction error flags complex, temporal anomalies.", className="support-card-text")
                                ])
                            ])
                        ]),

                        # Section 2: Interpret & Troubleshoot
                        html.Div(className="support-section", children=[
                            html.Div(className="support-section-header", style={"textAlign": "left", "alignItems": "flex-start"}, children=[
                                html.H2("Interpret & Troubleshoot", className="support-h2")
                            ]),
                            html.Div(className="support-grid-2", children=[
                                # Left 
                                html.Div(className="support-left-col", children=[
                                    html.Div(className="support-card support-card-row", children=[
                                        html.Div(className="support-card-header", children=[
                                            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23F5A623' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z'%3E%3C/path%3E%3Cline x1='12' y1='9' x2='12' y2='13'%3E%3C/line%3E%3Cline x1='12' y1='17' x2='12.01' y2='17'%3E%3C/line%3E%3C/svg%3E"), 
                                            html.H4("Anomaly ≠ Trading Signal")
                                        ]),
                                        html.P("This system detects statistical deviations, not future price movements. Action should be taken carefully based on broader quantitative strategies.", className="support-card-text")
                                    ]),
                                    html.Div(className="support-card support-card-row", children=[
                                        html.Div(className="support-card-header", children=[
                                            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23FF5A5F' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Ccircle cx='12' cy='12' r='6'%3E%3C/circle%3E%3Ccircle cx='12' cy='12' r='2'%3E%3C/circle%3E%3C/svg%3E"), 
                                            html.H4("Why an Ensemble Logic?")
                                        ]),
                                        html.P("Individual algorithms are prone to false positives. A hard anomaly is only flagged if ≥ 2 distinct models agree, ensuring a robust low false-positive rate.", className="support-card-text")
                                    ]),
                                    html.Div(className="support-card support-card-row", children=[
                                        html.Div(className="support-card-header", children=[
                                            html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%232ecc71' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'%3E%3C/polygon%3E%3C/svg%3E"), 
                                            html.H4("What does 'Inject Anomaly' do?")
                                        ]),
                                        html.P("Located in the sidebar, this safely simulates a massive market crash (price wipe + volume surge) to demonstrate the system's live reaction capabilities instantly.", className="support-card-text")
                                    ])
                                ]),
                                # Right
                                html.Div(className="support-card support-big-card", children=[
                                    html.Div(className="support-big-icon-wrap", children=[
                                        html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%234A90E2' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'%3E%3C/path%3E%3Cpolyline points='14 2 14 8 20 8'%3E%3C/polyline%3E%3Cline x1='16' y1='13' x2='8' y2='13'%3E%3C/line%3E%3Cline x1='16' y1='17' x2='8' y2='17'%3E%3C/line%3E%3Cpolyline points='10 9 9 9 8 9'%3E%3C/polyline%3E%3C/svg%3E")
                                    ]),
                                    html.H3("Exporting Terminal Intelligence", className="support-big-title"),
                                    html.P("Generate high-fidelity PDF reports for board review. Our offline rendering engine snapshots every chart, weighting and trace element cleanly.", className="support-card-text", style={"marginBottom": "24px"}),
                                    
                                    html.Div(className="support-steps", children=[
                                        html.Div(className="support-step", children=[
                                            html.Span("1", className="step-num"), 
                                            html.Span("Ensure anomalous data is currently visible in the active log overview overlay.", className="step-text")
                                        ]),
                                        html.Div(className="support-step", children=[
                                            html.Span("2", className="step-num"), 
                                            html.Span("Click the bright blue 'EXPORT PDF' generation button located natively in the top header.", className="step-text")
                                        ]),
                                        html.Div(className="support-step", children=[
                                            html.Span("3", className="step-num"), 
                                            html.Span("Receive an automated direct download of the PDF within 45 seconds natively through the browser window.", className="step-text")
                                        ])
                                    ])
                                ])
                            ])
                        ])
                    ]),
                    # Status Bar
                    html.Div(
                        className="statusbar",
                        children=[
                            html.Span(className="statusbar-dot"),
                            html.Span("SYSTEM OPERATIONAL"),
                            html.Span("V3.4.1-Stable", style={"marginLeft": "8px", "opacity": "0.6"}),
                        ],
                    ),

                    # Hidden Interval
                    dcc.Interval(
                        id="update-interval",
                        interval=config.DASH_UPDATE_INTERVAL_MS,
                        n_intervals=0,
                    ),
                ],
            ),

            # ── Modal ────────────────────────────────────────
            html.Div(
                id="anomaly-modal-overlay",
                className="modal-overlay hidden",
                children=[
                    html.Div(
                        className="modal-content",
                        children=[
                            html.Div(
                                className="modal-header",
                                children=[
                                    html.H3("LOG ENTRY DETAIL", id="modal-title"),
                                    html.Button("X", id="close-modal-btn", className="modal-close-btn"),
                                ],
                            ),
                            html.Div(id="modal-body", className="modal-body"),
                        ],
                    ),
                ],
            ),
        ],
    )

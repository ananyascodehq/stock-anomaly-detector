import re

with open('dashboard/layout.py', 'r', encoding='utf-8') as f:
    layout_content = f.read()

# Replace dashboard button
layout_content = layout_content.replace(
'''                            html.Div(
                                className="sidebar-nav-item active",
                                children=[
                                    html.Div(className="sidebar-nav-icon"''',
'''                            html.Div(
                                className="sidebar-nav-item active",
                                id="nav-dashboard-btn",
                                n_clicks=0,
                                style={"cursor": "pointer"},
                                children=[
                                    html.Div(className="sidebar-nav-icon"'''
)

# Replace Support button with SVG
layout_content = layout_content.replace(
'''                            html.Div(
                                className="sidebar-support",
                                children=[
                                    html.Span("?"),
                                    html.Span("Support"),
                                ],
                            ),''',
'''                            html.Div(
                                className="sidebar-support",
                                id="nav-support-btn",
                                n_clicks=0,
                                style={"cursor": "pointer"},
                                children=[
                                    html.Img(src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%239DA7B3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'%3E%3C/path%3E%3Cline x1='12' y1='17' x2='12.01' y2='17'%3E%3C/line%3E%3C/svg%3E", style={"marginRight": "4px"}),
                                    html.Span("Support"),
                                ],
                            ),'''
)

wrapper_start = '                    html.Div(id="dashboard-view", style={"display": "flex", "flexDirection": "column", "gap": "24px"}, children=[\n'
wrapper_end = '                    ]),\n'

support_block = '''                    html.Div(id="support-view", style={"display": "none", "flexDirection": "column", "gap": "24px"}, children=[
                        html.Div(className="page-header", children=[
                            html.H1("System Documentation & Support", className="page-header-title")
                        ]),
                        html.Div(className="card", children=[
                            html.H3("What is the Stock Market?", style={"color": "#E6EDF3", "marginBottom": "10px", "fontSize": "16px"}),
                            html.P("The stock market is where buyers and sellers trade shares of publicly held companies. It can be highly volatile, experiencing rapid price drops (flash crashes) or surges due to macroeconomic factors, algorithmic trading, or breaking news.", style={"color": "#9DA7B3", "lineHeight": "1.6", "marginBottom": "20px", "fontSize": "13px"}),
                            
                            html.H3("Objective of this Product", style={"color": "#E6EDF3", "marginBottom": "10px", "fontSize": "16px"}),
                            html.P("This platform serves as an early-warning radar for quantitative analysts. By continuously monitoring live order book and price mechanics, it detects statistically impossible deviations and structural breaks in market behavior before they become apparent to the human eye.", style={"color": "#9DA7B3", "lineHeight": "1.6", "marginBottom": "20px", "fontSize": "13px"}),
                            
                            html.H3("Data Source", style={"color": "#E6EDF3", "marginBottom": "10px", "fontSize": "16px"}),
                            html.P("Real-time data feeds are simulated via Yahoo Finance utilizing strictly 1-minute (1m) polling intervals to construct the Open-High-Low-Close-Volume (OHLCV) timeseries dataframe.", style={"color": "#9DA7B3", "lineHeight": "1.6", "fontSize": "13px"}),
                        ]),
                        html.Div(className="card", children=[
                            html.H3("Diagnostic Models Deployed", style={"color": "#E6EDF3", "marginBottom": "14px", "fontSize": "16px"}),
                            
                            html.H4("1. Z-Score (Statistical Deviation)", style={"color": "#4A90E2", "marginBottom": "5px", "fontSize": "14px"}),
                            html.P("Measures exactly how many standard deviations the current volume and price returns are straying from their rolling mean. Used to catch aggressive, blunt-force volatility shocks instantaneously.", style={"color": "#9DA7B3", "lineHeight": "1.6", "marginBottom": "15px", "fontSize": "13px"}),

                            html.H4("2. Isolation Forest (Outlier Detection)", style={"color": "#4A90E2", "marginBottom": "5px", "fontSize": "14px"}),
                            html.P("An unsupervised machine learning algorithm that isolates anomalous datapoints by randomly slicing systemic feature dimensions. Used because it is incredibly effective at identifying multi-dimensional outliers (e.g., normal price but entirely broken volume spread metrics).", style={"color": "#9DA7B3", "lineHeight": "1.6", "marginBottom": "15px", "fontSize": "13px"}),

                            html.H4("3. LSTM Autoencoder (Sequence Anomaly)", style={"color": "#4A90E2", "marginBottom": "5px", "fontSize": "14px"}),
                            html.P("A deep learning neural network trained to perfectly reconstruct normal, healthy chronological market sequences. When encountering bizarre, unprecedented temporal behavior, its reconstruction error heavily spikes. Used strictly to identify toxic underlying sequential patterns.", style={"color": "#9DA7B3", "lineHeight": "1.6", "marginBottom": "20px", "fontSize": "13px"}),

                            html.H3("Ensemble Consensus Logic", style={"color": "#E6EDF3", "marginBottom": "10px", "fontSize": "16px"}),
                            html.P("Single mathematical models are prone to false positives. To combat this, the system mandates an 'Ensemble Logic'. A hard system anomaly is flagged if and only if ≥ 2 distinct models agree simultaneously. This acts as a robust voting paradigm ensuring incredibly low false-positive rates.", style={"color": "#9DA7B3", "lineHeight": "1.6", "fontSize": "13px"}),
                        ]),
                        html.Div(className="card", children=[
                            html.H3("Understanding the UI & Alerts", style={"color": "#E6EDF3", "marginBottom": "14px", "fontSize": "16px"}),
                            html.Div("⚠️ Anomaly ≠ trading signal. This system detects statistical deviations, not future price movements.", style={"backgroundColor": "rgba(245,166,35,0.1)", "borderLeft": "3px solid #F5A623", "color": "#F5A623", "padding": "12px", "borderRadius": "4px", "fontWeight": "600", "marginBottom": "24px", "fontSize": "13px"}),
                            
                            html.H3("The 'Inject Anomaly' Button", style={"color": "#E6EDF3", "marginBottom": "10px", "fontSize": "16px"}),
                            html.P("A debugging toggle located in the sidebar. Since actual statistical market crashes are extremely rare, this button artificially injects a simulated massive crash (15% price wipe + 50x volume surge) directly into the datastream. It executes on the next polling cycle, immediately triggering all models to demonstrate the system's reaction capability.", style={"color": "#9DA7B3", "lineHeight": "1.6", "fontSize": "13px"}),
                        ]),
                    ]),
'''

parts = layout_content.split('                    # Page Header')
top = parts[0]
rem = '                    # Page Header' + parts[1]

parts2 = rem.split('                    # Status Bar')
middle = parts2[0]
bot = '                    # Status Bar' + parts2[1]

final_content = top + wrapper_start + middle + wrapper_end + support_block + bot

with open('dashboard/layout.py', 'w', encoding='utf-8') as f:
    f.write(final_content)

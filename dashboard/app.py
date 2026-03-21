import dash
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dashboard.layout import create_layout

app = dash.Dash(
    __name__,
    title="Stock Anomaly Detector",
    update_title="Loading Data...",
    assets_folder=os.path.join(os.path.dirname(__file__), "assets"),
)

app.layout = create_layout(app)

import dashboard.callbacks

def create_app():
    return app

if __name__ == '__main__':
    app.run(debug=True, port=8050)

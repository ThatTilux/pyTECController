from dash import dash_table, html, dcc
import dash_bootstrap_components as dbc

from ui.components.download_accordion import download_accordion
from ui.components.graphs import graphs

layout = dbc.Container(
    [
        html.H1("TEC Data Display"),
        dash_table.DataTable(id="tec-data-table"),
        graphs(),
        download_accordion(),
        dcc.Download(id="download-data-csv"),
        dcc.Store(id="store-tec-data"),  # storing the TEC data
        dcc.Interval(id="interval-component", interval=1 * 1000, n_intervals=0),  # 1s
    ]
)

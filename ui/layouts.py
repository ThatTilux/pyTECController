from dash import html, dcc
import dash_bootstrap_components as dbc


from ui.components.control_form import control_form
from ui.components.data_table import data_table
from ui.components.download_accordion import download_accordion
from ui.components.graphs import graphs

layout = dbc.Container(
    [
        html.H1("TEC Central Command Control"),
        control_form(),
        data_table(),
        graphs(),
        download_accordion(),
        dcc.Download(id="download-data-csv"),
        dcc.Store(id="store-tec-data"),  # storing the TEC data
        dcc.Interval(id="interval-component", interval=1 * 1000, n_intervals=0),  # 1s
    ], class_name="pt-2"
)

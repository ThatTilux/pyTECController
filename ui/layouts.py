from dash import html, dcc
import dash_bootstrap_components as dbc


from ui.components.control_form import control_form
from ui.components.data_table import data_table
from ui.components.download_accordion import download_accordion
from ui.components.graphs import graphs

layout = dbc.Container(
    [
        html.H1("TEC Central Command Control"),
        html.H3(
            "Dummy Mode: Could not establish a connection to the TECs. Using dummy data instead.",
            style={"display": "none"},
            id="dummy-mode-heading"
        ),
        control_form(),
        data_table(),
        graphs(),
        download_accordion(),
        dcc.Download(id="download-data-csv"),
        dcc.Interval(id="interval-component", interval=2 * 1000, n_intervals=0),  # 2s
        dcc.Interval(id="interval-dummy-detection", interval=5 * 1000, n_intervals=0, max_intervals=5),  # 5s, stop after 5 excecutions
    ],
    class_name="pt-2",
)

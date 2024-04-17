from dash import html, dcc
import dash_bootstrap_components as dbc


from ui.components.control_form import control_form
from ui.components.data_table import data_table
from ui.components.download_accordion import download_accordion
from ui.components.graphs import graphs


def layout(app):
    return dbc.Container(
        [
            html.H1("TEC Central Command Control"),
            # will be displayed in case of dummy-mode
            html.H3(
                "Dummy Mode: Could not establish a connection to the TECs. Using dummy data instead.",
                style={"display": "none"},
                id="dummy-mode-heading",
            ),
            # form to control the target temperature and start/stop the TECs
            control_form(),
            # shows the most recent measurement
            data_table(),
            # various graphs that display the data
            graphs(app),
            # accordion at the bottom of the page
            download_accordion(),
            # handles the download
            dcc.Download(id="download-data-csv"),
            # interval for updating all the data displays
            dcc.Interval(
                id="interval-component", interval=2 * 1000, n_intervals=0
            ),  # 2s
            # interval for dummy detection
            dcc.Interval(
                id="interval-dummy-detection",
                interval=5 * 1000,
                n_intervals=0,
                max_intervals=5,
            ),  # 5s, stop after 5 excecutions
            html.Div(
                id="dummy-output", style={"display": "none"}
            ),  # div for dummy callback outputs
        ],
        class_name="pt-2",
    )

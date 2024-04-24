from dash import html, dcc
import dash_bootstrap_components as dbc


from ui.components.control_form import control_form
from ui.components.data_table import data_table
from ui.components.download_accordion import download_accordion
from ui.components.graphs import graphs
from ui.components.sequence_control_box import sequence_control_box


def layout(app):
    return dbc.Container(
        [
            html.H1("TEC Central Command Control"),
            # will be displayed in case of dummy-mode
            html.Div(
                html.H3(
                    "Dummy Mode: Could not establish a connection to the TECs. Using dummy data instead.",
                    style={"color": "red"},
                ),
                id="dummy-mode-container",
                style={"display": "none"},
            ),
            dbc.Tabs(
                [
                    # form to control the target temperature and start/stop the TECs
                    dbc.Tab(html.Div(control_form(), className="mt-3"), label="Temperature Control"),
                    # creation and starting of sequences
                    dbc.Tab(html.Div(sequence_control_box(), className="mt-3"), label="Sequence"),
                ]
            ),
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
                interval=1 * 1000,
                n_intervals=0,
                max_intervals=5,
            ),  # 1s, stop after 10 excecutions
            # store for holding the indices of visible rows in the sequence manager
            dcc.Store(id="visible-sequence-rows", data=[0]),
        ],
        class_name="pt-2",
    )

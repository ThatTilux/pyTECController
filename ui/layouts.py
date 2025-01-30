from dash import html, dcc
import dash_bootstrap_components as dbc


from ui.components.welcome_menu import welcome_menu, welcome_menu_toast
from ui.components.control_form import control_form
from ui.components.data_table import data_table
from ui.components.download_accordion import download_accordion
from ui.components.graphs import graphs
from ui.components.initial_load_spinner import initial_load_spinner
from ui.components.sequence_control_box import sequence_control_box
from ui.components.tec_error_page import tec_error_page


# preconfigured sequence that will show up on startup
PRECONFIGURED_SEQUENCE_DATA = {
    "0": [65, 65, 1, 60],
    "1": [65, 50, 3, 45],
    "2": [45, 30, 20, 45],
    "3": [30, 30, 1, 1],
}

# holding info on what mode is currently active ("None" -> show welcome, "Dummy" -> show dummy mode, "Normal" -> show normal mode)
ACTIVE_MODE = "None"


def layout(app):
    return html.Div(
        children=[
            tec_error_page(),
            dbc.Container(
                [
                    welcome_menu_toast(),
                    html.H1("TEC Central Command Control"),
                    # will be displayed in case of dummy-mode
                    html.Div(
                        html.H3(
                            "Dummy Mode. Showing pre-recorded data.",
                            style={"color": "red"},
                        ),
                        id="dummy-mode-container",
                        style={"display": "none"},
                    ),
                    # loading indicator on app startup
                    initial_load_spinner(),
                    # welcome menu
                    html.Div(
                        id="welcome-menu",
                        style={"display": "none"},  # hide initially
                        children=[
                            welcome_menu(),
                        ],
                    ),
                    # app main content
                    html.Div(
                        id="app-main-content",
                        style={"display": "none"},  # hide initially
                        children=[
                            dbc.Tabs(
                                [
                                    # form to control the target temperature and start/stop the TECs
                                    dbc.Tab(
                                        html.Div(control_form(), className="mt-3"),
                                        label="Temperature Control",
                                    ),
                                    # creation and starting of sequences
                                    dbc.Tab(
                                        html.Div(
                                            sequence_control_box(), className="mt-3"
                                        ),
                                        label="Sequence",
                                    ),
                                ]
                            ),
                            # shows the most recent measurement
                            data_table(),
                            # various graphs that display the data
                            graphs(app),
                            # accordion at the bottom of the page
                            download_accordion(),
                        ],
                    ),
                    # handles the download
                    dcc.Download(id="download-data-csv"),
                    # interval for updating all the data displays
                    dcc.Interval(
                        id="interval-component", interval=2 * 1000, n_intervals=0
                    ),  # 2s
                    # store for holding the indices and content of visible rows in the sequence manager
                    dcc.Store(
                        id="visible-sequence-rows",
                        data=PRECONFIGURED_SEQUENCE_DATA,
                        storage_type="session",
                    ),  # keys are strings since dash store will convert them to str anywys
                    # store for holding info on whether or not a sequence is running
                    dcc.Store(
                        id="is-sequence-running", data=False, storage_type="session"
                    ),
                    # hidden div to track whether the app is ready to be displayed
                    html.Div(
                        id="initial-load", style={"display": "none"}, children="Loaded."
                    ),
                ],
                class_name="pt-2",
            ),
        ]
    )

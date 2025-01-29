from datetime import datetime
from dash import callback_context as ctx
from dash.dependencies import Output, Input, State
from dash import dcc, no_update
import dash_bootstrap_components as dbc
import dash

from app.serial_ports import PORTS
from ui.callbacks.graphs_tables import (
    is_graph_paused,
    set_pause_sequence,
    skip_sequence_step,
)
from ui.command_sender import (
    disable_all_plates,
    enable_all_plates,
    set_temperature,
    start_backend,
    start_backend_dummy,
)
from ui.components.connection_status_row import connection_status_row
from ui.data_store import (
    get_callback_lock,
    get_connection_status,
    get_data_both_channels,
    get_data_for_download,
    get_recovered_data,
    set_callback_lock,
)

from ui.layouts import ACTIVE_MODE

# Helper function to get the file name of a new CSV to be downloaded as a string
def get_CSV_file_name():
    time = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    return f"TEC_data_{time}.csv"


def button_callbacks(app):
    # combined callback for when the start backend btn is pressed or the page is loaded for the first time
    @app.callback(
        [
            Output("welcome-menu", "style"),
            Output("modal-connect-tecs", "is_open"),
            Output("app-main-content", "style"),
            Output("dummy-mode-container", "style"),
            Output("toast-start-backend-error", "is_open"),
            Output("spinner-btn-start-backend", "children"),  # to trigger its spinner
            Output("initial-load-spinner", "style"),  # Added for spinner logic
        ],
        [
            Input("btn-start-backend", "n_clicks"),
            Input("btn-start-backend-dummy", "n_clicks"),
            Input("initial-load", "children"),
        ],
        prevent_initial_call=False,  # Allow initial execution
    )
    def combined_callback(n_clicks_backend, n_clicks_dummy, is_loaded):
        # Define return values for normal and dummy mode
        return_normal = (
            {"display": "none"},
            False,
            {"display": "block"},
            {"display": "none"},
            no_update,
            no_update,
            {"display": "none"},  # Hide spinner
        )

        return_dummy = (
            {"display": "none"},
            False,
            {"display": "block"},
            {"display": "block"},
            no_update,
            no_update,
            {"display": "none"},  # Hide spinner
        )

        # Check if this is the initial call (e.g., page reload)
        if not ctx.triggered:  
            # Restore previous state if backend is already running
            global ACTIVE_MODE
            if ACTIVE_MODE == "Normal":
                return return_normal
            elif ACTIVE_MODE == "Dummy":
                return return_dummy
            elif ACTIVE_MODE == "None":
                return no_update
            else:
                raise ValueError(f"Invalid active mode: {ACTIVE_MODE}")

        # Determine which component triggered the callback
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Handle spinner logic on initial load
        if triggered_id == "initial-load":
            if is_loaded:
                return {"display": "block"}, no_update, no_update, no_update, no_update, no_update, {"display": "none"}  # Hide spinner, show welcome menu
            else:
                return {"display": "none"}, no_update, no_update, no_update, no_update, no_update, {"display": "block"}  # Show spinner, hide welcome menu

        # Backend Start Button Pressed
        elif triggered_id == "btn-start-backend":
            success = start_backend()
            if success:
                ACTIVE_MODE = "Normal"
                return return_normal

        elif triggered_id == "btn-start-backend-dummy":
            success = start_backend_dummy()
            if success:
                ACTIVE_MODE = "Dummy"
                return return_dummy

        # An error occurred, show error toast
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            True,  # Show error toast
            no_update,
            no_update,  # Keep spinner state unchanged
        )

    # callback for when the refresh connection status btn is pressed
    @app.callback(
        [
            Output("connection-status-container", "children"),
            Output("btn-start-backend", "disabled"),
        ],
        Input("btn-refresh-tec-connection-status", "n_clicks"),
        prevent_initial_call=False,
    )
    def refresh_connection_status(n_clicks):
        # check that this callback is not already running to prevent btn spamming
        if get_callback_lock("refresh_connection_status"):
            return dash.no_update

        # set callback lock
        set_callback_lock("refresh_connection_status", True)

        # try-finally block for the rest of the code to make sure that the lock is unset in every case
        try:

            connection_status = get_connection_status()
            if connection_status is None:
                return dash.no_update

            updated_rows = []

            connection_ready = True

            for label, status in connection_status.items():
                try:
                    port = PORTS[label]
                except KeyError:
                    print(f"[WARNING] Port {label} not found in PORTS")
                    continue

                updated_rows.append(connection_status_row(label, port, status))
                if not status and "OPTIONAL" not in label:
                    connection_ready = False

            return updated_rows, not connection_ready
        finally:
            # unset callback lock
            set_callback_lock("refresh_connection_status", False)

    # when the download data btn is pressed
    @app.callback(
        Output("download-data-csv", "data"),
        [
            Input("btn-download-csv", "n_clicks"),
            Input("btn-download-csv-reconnecting", "n_clicks"),
            State("checkboxes-download", "value"),
        ],
        prevent_initial_call=True,
    )
    def download_all_data(n, n2, selected_options):
        # Check which button was pressed
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "btn-download-csv-reconnecting":
            # Select all options
            selected_options = None

        df = get_data_for_download(selected_options)

        return dcc.send_data_frame(df.to_csv, get_CSV_file_name())

    # when the recover data btn is pressed
    @app.callback(
        Output("download-data-csv", "data", allow_duplicate=True),
        Input("btn-download-recovered-csv", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_recovered_data(n_clicks):
        df = get_recovered_data()

        return dcc.send_data_frame(df.to_csv, get_CSV_file_name())

    # when the pause graphs btn is pressed
    # the actual pausing happens in the callback that updates the graphs
    @app.callback(
        [
            Output("btn-pause-graphs", "children"),
            Output("btn-pause-graphs-2", "children"),
        ],
        [
            Input("btn-pause-graphs", "n_clicks"),
            Input("btn-pause-graphs-2", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def handle_pause_graphs(n_clicks, n_clicks_2):
        btn_label = (
            "Resume Graphs"
            if is_graph_paused(n_clicks, n_clicks_2)
            else "Freeze Graphs"
        )

        return btn_label, btn_label

    # callback for when the pause sequence btn is pressed
    @app.callback(
        Output("btn-pause-sequence", "children"),
        Input("btn-pause-sequence", "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_pause_sequence(n_clicks):
        paused = n_clicks % 2 == 1

        # notify the sequence manager
        set_pause_sequence(paused)

        # return btn label
        if paused:
            return "Resume Sequence"
        return "Pause Sequence"

    # callback for when the skip sequence btn is pressed
    @app.callback(
        Output("btn-skip-sequence-step", "n_clicks"),  # dummy
        Input("btn-skip-sequence-step", "n_clicks"),
        prevent_initial_call=True,
    )
    def skip_step(n_clicks):
        # send the skip
        skip_sequence_step()

        return dash.no_update

    # when the stop all tecs btn is pressed
    @app.callback(
        Output("btn-stop-all-tecs", "n_clicks"),  # dummy
        [Input("btn-stop-all-tecs", "n_clicks")],
        prevent_initial_call=True,
    )
    def stop_tecs(n_clicks):
        disable_all_plates()
        return dash.no_update

    # when the start btn is pressed
    @app.callback(
        [
            Output(
                {"type": "set-target-temp-error", "index": "input-top-plate"},
                "children",
            ),
            Output(
                {"type": "set-target-temp-error", "index": "input-bottom-plate"},
                "children",
            ),
        ],
        [
            Input("btn-start-tecs", "n_clicks"),
            State({"type": "set-target-temp", "index": "input-top-plate"}, "value"),
            State({"type": "set-target-temp", "index": "input-bottom-plate"}, "value"),
        ],
        prevent_initial_call=True,
    )
    def start_tecs(n_clicks, top_temp, bottom_temp):
        # the number input ensures that the temps are int or float or None

        # check if the fields were filled
        error_top = ""
        error_bottom = ""
        if top_temp is None:
            error_top = "Please enter a temperature."

        if bottom_temp is None:
            error_bottom = "Please enter a temperature."

        if not error_top and not error_bottom:
            top_temp = float(top_temp)
            bottom_temp = float(bottom_temp)

            # set temps and start all tecs
            set_temperature("top", top_temp)
            set_temperature("bottom", bottom_temp)

            enable_all_plates()

        return error_top, error_bottom

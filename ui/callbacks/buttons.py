from datetime import datetime
from dash import callback_context as ctx
from dash.dependencies import Output, Input, State, ALL
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


# variable to keep track of the last state of optional TEC controller's switches
_switches_state = []


# Helper function to get the file name of a new CSV to be downloaded as a string
def get_CSV_file_name():
    time = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    return f"TEC_data_{time}.csv"


# Helper function to assess the disabled state of the 'start' btn in welcome menu and build the rows
def helper_build_rows_and_check_disabled(switches, labels):
    # get state of optional TEC contorller's switches
    optional_tec_controllers = {}
    for switch, label in zip(switches, labels):
        optional_tec_controllers[label] = switch

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

        # retain the switch value for optional TEC controllers
        if label in optional_tec_controllers.keys():
            switch_value = optional_tec_controllers[label]
        else:
            switch_value = True

        updated_rows.append(connection_status_row(label, port, status, switch_value))
        if not status:
            # optional TEC controllers that are toggled off do not count as a connection error
            if "OPTIONAL" in label and (
                label not in optional_tec_controllers.keys()
                or optional_tec_controllers[label]
            ):  # by default, switches are True
                connection_ready = False
            elif "OPTIONAL" not in label:
                connection_ready = False
    return updated_rows, not connection_ready


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
            Output("graph-external-temperature-container", "style") 
        ],
        [
            Input("btn-start-backend", "n_clicks"),
            Input("btn-start-backend-dummy", "n_clicks"),
            Input("initial-load", "children"),
        ],
        [
            State(
                {"type": "toggle-tec-controller", "index": ALL}, "value"
            ),  # all switches for optional TEC controllers
            State(
                {"type": "toggle-tec-controller", "index": ALL}, "label_id"
            ),  # name/label of the TEC controller in PORTS
        ],
        prevent_initial_call=False,  # Allow initial execution
    )
    def combined_callback(n_clicks_backend, n_clicks_dummy, is_loaded, optionals_switches, optionals_switches_labels):
        # check if at least one external is active
        has_external = True in optionals_switches
        external_container_style = {"display": "block"} if has_external else {"display": "none"}
        
        # Define return values for normal and dummy mode
        return_normal = (
            {"display": "none"},
            False,
            {"display": "block"},
            {"display": "none"},
            no_update,
            no_update,
            {"display": "none"},  # Hide spinner
            external_container_style
        )

        return_dummy = (
            {"display": "none"},
            False,
            {"display": "block"},
            {"display": "block"},
            no_update,
            no_update,
            {"display": "none"},  # Hide spinner
            {"display": "none"} # hardcode that dummy data has no external temperature here
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
                return (
                    {"display": "block"},
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {"display": "none"},
                    no_update,
                )  # Hide spinner, show welcome menu
            else:
                return (
                    {"display": "none"},
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    {"display": "block"},
                    no_update,
                )  # Show spinner, hide welcome menu

        # Backend Start Button Pressed
        elif triggered_id == "btn-start-backend":
            # get the list of optional TEC controllers to connect to
            optional_tec_controllers = []
            for switch, label in zip(optionals_switches, optionals_switches_labels):
                if switch:
                    optional_tec_controllers.append(label)
            
            success = start_backend(optional_tec_controllers)
            
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
            no_update, 
        )

    # callback for when the refresh connection status btn is pressed
    @app.callback(
        [
            Output("connection-status-container", "children"),
            Output("btn-start-backend", "disabled"),
        ],
        [
            Input("btn-refresh-tec-connection-status", "n_clicks"),
        ],
        [
            State(
                {"type": "toggle-tec-controller", "index": ALL}, "value"
            ),  # all switches for optional TEC controllers
            State(
                {"type": "toggle-tec-controller", "index": ALL}, "label_id"
            ),  # name/label of the TEC controller in PORTS
        ],
        prevent_initial_call=False,
    )
    def refresh_connection_status(n_clicks, switches, labels):
        # check that this callback is not already running to prevent btn spamming
        if get_callback_lock("refresh_connection_status"):
            return dash.no_update

        # set callback lock
        set_callback_lock("refresh_connection_status", True)

        # try-finally block for the rest of the code to make sure that the lock is unset in every case
        try:
            return helper_build_rows_and_check_disabled(switches, labels)
        finally:
            # unset callback lock
            set_callback_lock("refresh_connection_status", False)

    # when a switch of an optional TEC controller is toggled
    @app.callback(
        Output("btn-start-backend", "disabled", allow_duplicate=True),
        [
            Input({"type": "toggle-tec-controller", "index": ALL}, "value"),
        ],
        [State({"type": "toggle-tec-controller", "index": ALL}, "label_id")],
        prevent_initial_call=True,
    )
    def toggle_optional_tec_controller(switches, labels):
        # if the switch values are the same as the old ones, this callback was triggered
        # by a re-render and not by a switch toggle
        global _switches_state
        if _switches_state == switches:
            raise dash.exceptions.PreventUpdate

        _switches_state = switches

        _, disabled = helper_build_rows_and_check_disabled(switches, labels)
        return disabled

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

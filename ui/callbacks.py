import base64
from datetime import datetime
import dash
from dash.dependencies import Output, Input, State
from dash import dcc
import pandas as pd
from app.serial_ports import NUM_TECS
from ui.command_sender import disable_all_plates, enable_all_plates, set_temperature
from ui.components.graphs import (
    format_timestamps,
    update_graph_all_current,
    update_graph_all_temperature,
    update_graph_all_voltage,
    update_graph_max_current,
    update_graph_object_temperature,
    update_graph_max_voltage,
)
from ui.data_store import (
    get_data_for_download,
    get_data_from_store,
    get_most_recent,
    update_store,
)


def update_table(_df):
    """
    Updates the current measurements in the table
    """
    # create a deep copy as the df is significantly manipulated here
    df = _df.copy(deep=True)

    _convert_timestamps(df)

    format_timestamps(df)

    # Columns to round with the decimal number
    columns_to_round = [
        ("object temperature", 2),
        ("output current", 4),
        ("output voltage", 4),
    ]

    # Round specified columns
    for col, decimal in columns_to_round:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.{decimal}f}")

    # custom labels
    column_labels = {
        "loop status": "Status",
        "object temperature": "Temperature (°C)",
        "target object temperature": "Target (°C)",
        "output current": "Current (A)",
        "output voltage": "Voltage (V)",
        "timestamp": "Time",
    }

    # Parse the loop status
    # Function to determine the loop status based on conditions
    def determine_status(row):
        if row["loop status"] == 0:
            return "Inactive"
        elif row["loop status"] == 1:
            if float(row["output current"]) <= 0:
                return "Heating"
            else:
                return "Cooling"
        elif row["loop status"] == 2:
            return "Stable"
        else:
            return "Unknown"

    # Apply the function to each row
    df["loop status"] = df.apply(determine_status, axis=1)

    # Create a 'Label' column
    df["Label"] = (
        df.index.get_level_values("Plate").str.upper()
        + "_"
        + df.index.get_level_values("TEC").astype(str)
    )

    # create column odering so label is first
    cols = ["Label"] + [col for col in df.columns if col != "Label"]

    # Preparing columns for the DataTable with updated labels
    columns = [{"name": column_labels.get(i, i), "id": i} for i in cols]
    data = df.to_dict("records")
    return data, columns


def _convert_timestamps(df):
    """
    Converts the timestamps into the datetime format and adds 2 hours for the time zone.
    """
    # convert Timestamp is a datetime type
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Adding 2 hours to each timestamp
    df["timestamp"] = df["timestamp"] + pd.Timedelta(hours=2)


def _is_graph_paused(n_clicks):
    """
    Determines whether the graphs are paused based on the number of clicks of the Pause Graphs btn.
    """

    if n_clicks is None:
        return False

    return n_clicks % 2 == 1


# all callbacks inside this function
def register_callbacks(app):
    @app.callback(  # handles the table and graphs
        [
            Output("tec-data-table", "data"),
            Output("tec-data-table", "columns"),
            Output("graph-object-temperature", "figure"),
            Output("graph-all-current", "figure"),
            Output("graph-all-voltage", "figure"),
            Output("graph-all-temperature", "figure"),
        ],
        [
            Input("interval-component", "n_intervals"),
            State("btn-pause-graphs", "n_clicks"),
        ],
    )
    def update_components_from_store(n, n_clicks):

        # only show this many datapoints:
        MAX_DP_OBJECT_TEMP = NUM_TECS * 10 * 60  # 10 min
        MAX_DP_CURRENT = NUM_TECS * 5 * 60  # 5 min
        MAX_DP_VOLTAGE = NUM_TECS * 5 * 60  # 5 min

        # get data
        df_all = get_data_from_store()

        if df_all is None:
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        # update table
        df_recent = df_all.tail(NUM_TECS)
        table_data, table_columns = update_table(df_recent)

        # If graphs are paused, do not update them
        if _is_graph_paused(n_clicks):
            return (
                table_data,
                table_columns,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        # Update graphs

        _convert_timestamps(df_all)

        graph_object_temp = update_graph_object_temperature(
            df_all.tail(MAX_DP_OBJECT_TEMP)
        )
        graph_all_current = update_graph_all_current(df_all.tail(MAX_DP_CURRENT))
        graph_all_voltage = update_graph_all_voltage(df_all.tail(MAX_DP_VOLTAGE))
        graph_all_temperature = update_graph_all_temperature(
            df_all.tail(MAX_DP_OBJECT_TEMP)
        )

        return (
            table_data,
            table_columns,
            graph_object_temp,
            graph_all_current,
            graph_all_voltage,
            graph_all_temperature,
        )

    @app.callback(
        Output("download-data-csv", "data"),
        [
            Input("btn-download-csv", "n_clicks"),
            State("checkboxes-download", "value"),
        ],
        prevent_initial_call=True,
    )
    def download_all_data(n_clicks, selected_options):
        df = get_data_for_download()

        # only keep selected columns and the timestamp
        selected_columns = selected_options + ["timestamp"]
        df = df[selected_columns]

        time = datetime.now()
        return dcc.send_data_frame(df.to_csv, f"TEC_data_{time}.csv")

    @app.callback(
        Output("btn-pause-graphs", "children"),
        [Input("btn-pause-graphs", "n_clicks")],
        prevent_initial_call=True,
    )
    def handle_pause_graphs(n_clicks):
        btn_label = "Resume Graphs" if _is_graph_paused(n_clicks) else "Freeze Graphs"

        return btn_label

    @app.callback(
        Output("btn-stop-all-tecs", "n_clicks"),  # dummy
        [Input("btn-stop-all-tecs", "n_clicks")],
        prevent_initial_call=True,
    )
    def stop_tecs(n_clicks):
        disable_all_plates()
        return dash.no_update

    @app.callback(
        Output("btn-start-tecs", "children"),  # dummy
        [
            Input("btn-start-tecs", "n_clicks"),
            State("input-top-plate", "value"),
            State("input-bottom-plate", "value"),
        ],
        prevent_initial_call=True,
    )
    def start_tecs(n_clicks, top_temp, bottom_temp):
        # the number input ensures that the type is int or float or None
        if top_temp is None or bottom_temp is None:
            return dash.no_update

        top_temp = float(top_temp)
        bottom_temp = float(bottom_temp)

        set_temperature("top", top_temp)
        set_temperature("bottom", bottom_temp)

        enable_all_plates()
        return dash.no_update

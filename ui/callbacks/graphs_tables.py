from dash.dependencies import Output, Input, State
import dash
import pandas as pd

from app.serial_ports import NUM_TECS
from ui.components.graphs import format_timestamps, update_graph_all_current, update_graph_all_temperature, update_graph_all_voltage, update_graph_object_temperature, update_graph_sum_power
from ui.data_store import get_data_from_store


def is_graph_paused(n_clicks):
    """
    Determines whether the graphs are paused based on the number of clicks of the Pause Graphs btn.
    """

    if n_clicks is None:
        return False

    is_paused = n_clicks % 2 == 1

    return is_paused


def _convert_timestamps(df):
    """
    Converts the timestamps into the datetime format and adds 2 hours for the time zone.
    """
    # convert Timestamp is a datetime type
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Adding 2 hours to each timestamp
    df["timestamp"] = df["timestamp"] + pd.Timedelta(hours=2)


def update_measurement_table(_df):
    """
    Updates the current measurements in the table
    """
    # create a deep copy as the df is significantly manipulated here
    df = _df.copy(deep=True)

    # convert timestamps to a human-readable format
    _convert_timestamps(df)
    format_timestamps(df)

    # Columns to round with the number of decimals
    columns_to_round = [
        ("object temperature", 2),
        ("output current", 4),
        ("output voltage", 4),
        ("output power", 2)
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
        "output power": "Power (W)",
        "timestamp": "Time",
    }

    # Parse the loop status
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

    # Parse the multiindex to a 'Label' column
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


def graphs_tables_callbacks(app):
    @app.callback(  # handles the measurements table and all graphs
        [
            Output("tec-data-table", "data"),
            Output("tec-data-table", "columns"),
            Output("graph-object-temperature", "figure"),
            Output("graph-all-current", "figure"),
            Output("graph-all-current-2", "figure"),
            Output("graph-all-voltage", "figure"),
            Output("graph-all-voltage-2", "figure"),
            Output("graph-all-temperature", "figure"),
            Output("graph-all-temperature-2", "figure"),
            Output("graph-sum-power", "figure"),
            Output("graph-sum-power-2", "figure"),
        ],
        [
            Input("interval-component", "n_intervals"),
            State("btn-pause-graphs", "n_clicks"),
            State("graph-tabs", "active_tab"),
            State("graph-tabs-2", "active_tab"),
        ],
        prevent_initial_call=True,
    )
    def update_components_from_store(n, n_clicks, active_tab, active_tab_2):

        # only show this many datapoints:
        MAX_DP_OBJECT_TEMP = NUM_TECS * 10 * 60  # 10 min
        MAX_DP_CURRENT = NUM_TECS * 5 * 60  # 5 min
        MAX_DP_VOLTAGE = NUM_TECS * 5 * 60  # 5 min
        MAX_DP_POWER = NUM_TECS * 10 * 60 # 10 min

        # get data
        df_all = get_data_from_store()

        if df_all is None:
            return (dash.no_update,) * 11

        # update table
        # get the most recent measurement
        df_recent = df_all.tail(NUM_TECS)
        table_data, table_columns = update_measurement_table(df_recent)

        # If graphs are paused, do not update them
        if is_graph_paused(n_clicks):
            return (table_data, table_columns) + (dash.no_update,) * 9

        # Update graphs

        # convert timestamps to datetime
        _convert_timestamps(df_all)

        # update main temperature graph
        graph_object_temp = update_graph_object_temperature(
            df_all.tail(MAX_DP_OBJECT_TEMP), fig_id="graph-object-temperature"
        )

        # from the tab graphs, only update the visible ones

        # tab-1
        graph_all_current = (
            update_graph_all_current(
                df_all.tail(MAX_DP_CURRENT), fig_id="graph-all-current"
            )
            if active_tab == "tab-current"
            else dash.no_update
        )
        graph_all_voltage = (
            update_graph_all_voltage(
                df_all.tail(MAX_DP_VOLTAGE), fig_id="graph-all-voltage"
            )
            if active_tab == "tab-voltage"
            else dash.no_update
        )
        graph_all_temperature = (
            update_graph_all_temperature(
                df_all.tail(MAX_DP_OBJECT_TEMP), fig_id="graph-all-temperature"
            )
            if active_tab == "tab-temperature"
            else dash.no_update
        )
        graph_sum_power = (
            update_graph_sum_power(
                df_all.tail(MAX_DP_POWER), fig_id="graph-sum-power"
            )
            if active_tab == "tab-power"
            else dash.no_update
        )

        # tab-2
        graph_all_current2 = (
            update_graph_all_current(
                df_all.tail(MAX_DP_CURRENT), fig_id="graph-all-current-2"
            )
            if active_tab_2 == "tab-current"
            else dash.no_update
        )
        graph_all_voltage2 = (
            update_graph_all_voltage(
                df_all.tail(MAX_DP_VOLTAGE), fig_id="graph-all-voltage-2"
            )
            if active_tab_2 == "tab-voltage"
            else dash.no_update
        )
        graph_all_temperature2 = (
            update_graph_all_temperature(
                df_all.tail(MAX_DP_OBJECT_TEMP), fig_id="graph-all-temperature-2"
            )
            if active_tab_2 == "tab-temperature"
            else dash.no_update
        )
        graph_sum_power2 = (
            update_graph_sum_power(
                df_all.tail(MAX_DP_POWER), fig_id="graph-sum-power-2"
            )
            if active_tab_2 == "tab-power"
            else dash.no_update
        )

        return (
            table_data,
            table_columns,
            graph_object_temp,
            graph_all_current,
            graph_all_current2,
            graph_all_voltage,
            graph_all_voltage2,
            graph_all_temperature,
            graph_all_temperature2,
            graph_sum_power,
            graph_sum_power2,
        )

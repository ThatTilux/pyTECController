from time import time
from dash.dependencies import Output, Input, State
import dash
import pandas as pd

from app.serial_ports import NUM_TECS
from ui.command_sender import disable_all_plates, enable_all_plates, set_temperature
from ui.components.graphs import (
    format_timestamps,
    update_graph_all_current,
    update_graph_all_temperature,
    update_graph_all_voltage,
    update_graph_object_temperature,
    update_graph_sum_power,
)
from ui.data_store import get_data_from_store
from ui.sequence_manager import SequenceManager


# the sequence manager
sequence_manager = SequenceManager(temperature_window=0.5)


def set_sequence(sequence_values):
    """
    Sets the sequence in the sequence manager and starts all TECs.

    Args:
            sequence_values (list[(float, float, float, float)]): List of tuples with values for top_target, bottom_target, num_steps, time_sleep
    """
    # pass the sequence
    sequence_manager.set_sequence(sequence_values)

    # get the first targets
    top_target = sequence_values[0][0]
    bottom_target = sequence_values[0][1]

    # set the targets
    set_temperature(plate="top", temp=float(top_target))
    set_temperature(plate="bottom", temp=float(bottom_target))

    # enable all
    enable_all_plates()


def set_pause_sequence(value):
    """
    Pauses / Unpauses the sequence
    """
    sequence_manager.set_paused(value)


def skip_sequence_step():
    """
    Skips the current step of the sequence.
    """
    sequence_manager.skip_step()


def handle_sequence_instructions(instructions):
    """
    Handles instructions from the sequence manager.
    """
    # None = noop
    if instructions:
        if instructions[0] == "stop":
            # trigger the stop
            disable_all_plates()
        elif instructions[0] == "target":
            # get the targets
            top_target = instructions[1][0]
            bottom_target = instructions[1][1]

            # set the targets
            set_temperature(plate="top", temp=float(top_target))
            set_temperature(plate="bottom", temp=float(bottom_target))


def get_avg_temps(df):
    """
    Will return the average temperatures for the top and bottom plate.
    Format: top_avg, bottom_avg
    """
    if "object temperature" not in df.columns:
        raise ValueError("DataFrame must include an 'object temperature' column")

    # Group by 'Plate' level calculate the mean of 'object temperature' for each group
    avg_temps = df["object temperature"].groupby(level="Plate").mean()

    # Extract the average temperatures for 'top' and 'bottom'
    top_avg = avg_temps.loc["top"]
    bottom_avg = avg_temps.loc["bottom"]

    return top_avg, bottom_avg


def stop_sequence():
    """
    Aborts the current sequence.
    """
    sequence_manager.delete_sequence()


def is_graph_paused(n_clicks, n_clicks_2):
    """
    Determines whether the graphs are paused based on the number of clicks of the two Pause Graphs btns.
    """
    if n_clicks is None:
        n_clicks = 0
    if n_clicks_2 is None:
        n_clicks_2 = 0

    is_paused = (n_clicks + n_clicks_2) % 2 == 1

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
        ("target object temperature", 2),
        ("output current", 4),
        ("output voltage", 4),
        ("output power", 2),
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
            Output("sequence-status-container", "children"),
            Output("initial-load", "children"),
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
            State("btn-pause-graphs-2", "n_clicks"),
            State("graph-tabs", "active_tab"),
            State("graph-tabs-2", "active_tab"),
            State("initial-load", "children"),
        ],
        prevent_initial_call=True,
    )
    def update_components_from_store(
        n, n_clicks, n_clicks_2, active_tab, active_tab_2, is_app_loaded
    ):

        # notify the spinnder that the app has loaded and is ready for display
        if is_app_loaded:
            app_loading_status = dash.no_update
        else:
            app_loading_status = "loaded"

        # only show this many datapoints:
        MAX_DP_OBJECT_TEMP = NUM_TECS * 10 * 60  # 10 min
        MAX_DP_CURRENT = NUM_TECS * 5 * 60  # 5 min
        MAX_DP_VOLTAGE = NUM_TECS * 5 * 60  # 5 min
        MAX_DP_POWER = NUM_TECS * 10 * 60  # 10 min

        # get data
        df_all = get_data_from_store()

        if df_all is None:
            return (dash.no_update,) * 13

        # update table
        # get the most recent measurement
        df_recent = df_all.tail(NUM_TECS)
        table_data, table_columns = update_measurement_table(df_recent)

        # get the current avergae temperatures
        avg_top, avg_bottom = get_avg_temps(df_recent)

        # get new instructions from the sequence manager
        instructions = sequence_manager.get_instructions(avg_top, avg_bottom)
        handle_sequence_instructions(instructions)

        # get the sequence status
        sequence_status = sequence_manager.get_status(avg_top, avg_bottom)

        # If graphs are paused, do not update them
        if is_graph_paused(n_clicks, n_clicks_2):
            return (
                table_data,
                table_columns,
                sequence_status,
                app_loading_status,
            ) + (dash.no_update,) * 9

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
            update_graph_sum_power(df_all.tail(MAX_DP_POWER), fig_id="graph-sum-power")
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
            sequence_status,
            app_loading_status,
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

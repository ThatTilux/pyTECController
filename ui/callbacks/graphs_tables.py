from dash.dependencies import Output, Input, State
import dash
import pandas as pd
import time

import app.param_values as params
from app.param_values import NUM_TECS
from ui.command_sender import disable_all_plates, enable_all_plates, set_temperature
from ui.components.graphs import (
    format_timestamps,
    update_graph_all_current,
    update_graph_all_temperature,
    update_graph_all_voltage,
    update_graph_external_temperature,
    update_graph_object_temperature,
    update_graph_sum_power,
)
from ui.data_store import (
    get_callback_lock,
    check_reconnecting,
    get_data_from_store,
    set_callback_lock,
)
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
    Converts the timestamps into the datetime format and adjusts for the system's local time offset.
    """
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Get local time offset in seconds
    offset_seconds = time.localtime().tm_gmtoff
    df["timestamp"] = df["timestamp"] + pd.Timedelta(seconds=offset_seconds)

    return df


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

    # for the externals, specify the channel
    df.loc[df["Label"].str.contains("EXTERNAL"), "Label"] = (
        # turn the trailing number n into f"{n//2} ({'CH1' if n%2==0 else 'CH2'})"
        df.loc[df["Label"].str.contains("EXTERNAL"), "Label"].str.replace(
            r"(\d+)$",
            lambda x: f"{int(x.group(1))//2} ({'CH1' if int(x.group(1))%2==0 else 'CH2'})",
            regex=True,
        )
    )

    # for external tecs, wipe these cols to avoid confusion
    cols_to_wipe = [
        "loop status",
        "target object temperature",
        "output current",
        "output voltage",
        "output power",
    ]
    for col in cols_to_wipe:
        df.loc[df["Label"].str.contains("EXTERNAL"), col] = "-"

    # create column odering so label is first
    cols = ["Label"] + [col for col in df.columns if col != "Label"]

    # push all rows containing "EXTENRAL" to the end
    df = df.sort_values(by="Label", key=lambda col: col.str.contains("EXTERNAL"))

    # Preparing columns for the DataTable with updated labels
    columns = [{"name": column_labels.get(i, i), "id": i} for i in cols]
    data = df.to_dict("records")
    return data, columns


def tail_exclude_external(df, num_rows):
    """
    Returns the last num_rows rows of the DataFrame excluding the external TECs.
    """
    return df.loc[~df.index.get_level_values("Plate").str.contains("external")].tail(
        num_rows
    )


def tail_only_external(df, num_rows):
    """
    Returns the last num_rows rows of the DataFrame only including the external TECs.
    """
    return df.loc[df.index.get_level_values("Plate").str.contains("external")].tail(
        num_rows
    )
    
def tail_and_external(df, num_rows, external_labels):
    """
    Returns the last num_rows rows of the DataFrame and some specified external TECs in two dataframes.
    
    Args:
        df (pd.DataFrame): The DataFrame to slice
        num_rows (int): The number of rows to return
        external_labels (list): List of external TEC labels to include (format is EXTERNAL_{n//2} ({'CH1' if n%2==0 else 'CH2'}))
    """
    if not external_labels:
        return tail_exclude_external(df, num_rows), None
    
    # convert labels to ids
    external_ids = [params.get_external_id_from_label(label) for label in external_labels]
    
    # get the rows that contain the external TECs
    external_rows = df.loc[df.index.get_level_values("Plate").str.contains("external")]
    
    # filter the rows
    external_rows = external_rows.loc[external_rows.index.get_level_values("TEC").isin(external_ids)]
    
    # get the rows that do not contain the external TECs
    non_external_rows = df.loc[~df.index.get_level_values("Plate").str.contains("external")]
    
    # take tail
    non_external_rows = non_external_rows.tail(num_rows)
    
    # take tail of external rows (cut off until timestamp of first row of non_external_rows)
    external_rows = external_rows.loc[external_rows["timestamp"] >= non_external_rows.iloc[0]["timestamp"]]
    
    return non_external_rows, external_rows


def graphs_tables_callbacks(app):
    @app.callback(  # handles the measurements table and all graphs
        [
            Output("tec-data-table", "data"),
            Output("tec-data-table", "columns"),
            Output("sequence-status-container", "children"),
            Output("initial-load", "children"),
            Output("graph-object-temperature", "figure"),
            Output("graph-object-temperature-external", "figure"),
            Output("graph-all-current", "figure"),
            Output("graph-all-current-2", "figure"),
            Output("graph-all-voltage", "figure"),
            Output("graph-all-voltage-2", "figure"),
            Output("graph-all-temperature", "figure"),
            Output("graph-all-temperature-2", "figure"),
            Output("graph-sum-power", "figure"),
            Output("graph-sum-power-2", "figure"),
            Output("tec-error-overlay", "style"),
        ],
        [
            Input("interval-component", "n_intervals"),
            State("btn-pause-graphs", "n_clicks"),
            State("btn-pause-graphs-2", "n_clicks"),
            State("graph-tabs", "active_tab"),
            State("graph-tabs-2", "active_tab"),
            State("initial-load", "children"),
            State("graph-object-temperature-external-probes", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_components_from_store(
        n, n_clicks, n_clicks_2, active_tab, active_tab_2, is_app_loaded, object_temp_external_probes
    ):

        # notify the spinner that the app has loaded and is ready for display
        if is_app_loaded:
            app_loading_status = dash.no_update
        else:
            app_loading_status = "loaded"

        # before getting data, check if the app should be overlayed with the "Reconnecting" overlay
        reconnecting_code = check_reconnecting()
        if reconnecting_code == 1:
            # display overlay
            return (dash.no_update,) * 14 + ({"display": "block"},)

        # only show this many datapoints:
        MAX_DP_OBJECT_TEMP = NUM_TECS * 10 * 60  # 10 min
        MAX_DP_CURRENT = NUM_TECS * 5 * 60  # 5 min
        MAX_DP_VOLTAGE = NUM_TECS * 5 * 60  # 5 min
        MAX_DP_POWER = NUM_TECS * 10 * 60  # 10 min

        MAX_DP_OBJECT_TEMP_EXTERNAL = params.num_external_tecs * 10 * 60  # 10 min

        # get data
        df_all = get_data_from_store()

        if df_all is None:
            return dash.no_update

        # check that this callback is not already running
        if get_callback_lock("update_components_from_store"):
            return dash.no_update

        # set the lock
        set_callback_lock("update_components_from_store", True)

        # try-finally block for the rest of the code to make sure that the lock is unset in every case
        try:
            # only show this many datapoints:
            MAX_DP_OBJECT_TEMP = NUM_TECS * 10 * 60  # 10 min
            MAX_DP_CURRENT = NUM_TECS * 5 * 60  # 5 min
            MAX_DP_VOLTAGE = NUM_TECS * 5 * 60  # 5 min
            MAX_DP_POWER = NUM_TECS * 10 * 60  # 10 min

            # get data
            df_all = get_data_from_store()

            if df_all is None:
                return dash.no_update

            # update table
            # get the most recent measurement
            df_recent = df_all.tail(NUM_TECS + params.num_external_tecs)
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
                ) + (dash.no_update,) * 11

            # Update graphs

            # convert timestamps to datetime
            _convert_timestamps(df_all)

            # update main temperature graph
            df, df_external = tail_and_external(df_all, MAX_DP_OBJECT_TEMP, object_temp_external_probes)
            graph_object_temp = update_graph_object_temperature(
                df=df,
                df_external=df_external,
                fig_id="graph-object-temperature",
            )

            # update external temperature graph if applicable
            if params.num_external_tecs > 0:
                graph_object_temp_external = update_graph_external_temperature(
                    tail_only_external(df_all, MAX_DP_OBJECT_TEMP_EXTERNAL),
                    fig_id="graph-object-temperature-external",
                )
            else:
                graph_object_temp_external = dash.no_update

            # from the tab graphs, only update the visible ones

            # tab-1
            graph_all_current = (
                update_graph_all_current(
                    tail_exclude_external(df_all, MAX_DP_CURRENT),
                    fig_id="graph-all-current",
                )
                if active_tab == "tab-current"
                else dash.no_update
            )
            graph_all_voltage = (
                update_graph_all_voltage(
                    tail_exclude_external(df_all, MAX_DP_VOLTAGE),
                    fig_id="graph-all-voltage",
                )
                if active_tab == "tab-voltage"
                else dash.no_update
            )
            graph_all_temperature = (
                update_graph_all_temperature(
                    tail_exclude_external(df_all, MAX_DP_OBJECT_TEMP),
                    fig_id="graph-all-temperature",
                )
                if active_tab == "tab-temperature"
                else dash.no_update
            )
            graph_sum_power = (
                update_graph_sum_power(
                    tail_exclude_external(df_all, MAX_DP_POWER),
                    fig_id="graph-sum-power",
                )
                if active_tab == "tab-power"
                else dash.no_update
            )

            # tab-2
            graph_all_current2 = (
                update_graph_all_current(
                    tail_exclude_external(df_all, MAX_DP_CURRENT),
                    fig_id="graph-all-current-2",
                )
                if active_tab_2 == "tab-current"
                else dash.no_update
            )
            graph_all_voltage2 = (
                update_graph_all_voltage(
                    tail_exclude_external(df_all, MAX_DP_VOLTAGE),
                    fig_id="graph-all-voltage-2",
                )
                if active_tab_2 == "tab-voltage"
                else dash.no_update
            )
            graph_all_temperature2 = (
                update_graph_all_temperature(
                    tail_exclude_external(df_all, MAX_DP_OBJECT_TEMP),
                    fig_id="graph-all-temperature-2",
                )
                if active_tab_2 == "tab-temperature"
                else dash.no_update
            )
            graph_sum_power2 = (
                update_graph_sum_power(
                    tail_exclude_external(df_all, MAX_DP_POWER),
                    fig_id="graph-sum-power-2",
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
                graph_object_temp_external,
                graph_all_current,
                graph_all_current2,
                graph_all_voltage,
                graph_all_voltage2,
                graph_all_temperature,
                graph_all_temperature2,
                graph_sum_power,
                graph_sum_power2,
                {"display": "none"},
            )
        finally:
            set_callback_lock("update_components_from_store", False)

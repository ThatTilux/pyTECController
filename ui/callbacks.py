import base64
from datetime import datetime
from io import StringIO
import io
import json
from time import sleep
import dash
from dash.dependencies import Output, Input, State
from dash import dcc
import pandas as pd
from tec_interface import TECInterface
from ui.components.graphs import (
    format_timestamps,
    update_graph_max_current,
    update_graph_object_temperature,
    update_graph_max_voltage,
)

_tec_interface: TECInterface = None

# timestamp of the last data pulled
_last_data_timestamp = None


def tec_interface():
    global _tec_interface
    if _tec_interface is None:
        _tec_interface = TECInterface()
    return _tec_interface


def df_to_base64(df):
    """
    Converts a dataframe to base64 for storage
    """
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=True) # includes index
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded

def base64_to_df(encoded):
    """
    Converts a base64 encoded dataframe back to a dataframe
    """
    data = base64.b64decode(encoded)
    buffer = io.BytesIO(data)
    df = pd.read_parquet(buffer)
    return df


def get_data_from_store(store_data, most_recent=True):
    """Parses the data store and returns a dataframe with the data

    Args:
        store_data (string): base64 data from the data store
        most_recent (bool, optional): When set to true, only the most recent measurement is returned. When set to false, all recorded measurements are returned. Defaults to True.
    """
    if store_data is None:
        return None

    # convert json to df
    df = base64_to_df(store_data)
    
    if df.empty:
        return df

    if most_recent:
        # get the most recent timestamp from the last row and return all rows with that one
        last_index = len(df) - 1
        most_recent_timestamp = df.iloc[last_index]["timestamp"]

        # Iterate backwards until a different timestamp is found
        for i in range(last_index, -1, -1):
            if df.iloc[i]["timestamp"] != most_recent_timestamp:
                # Slice from the next index to the end to get all rows with the most recent timestamp
                return df.iloc[i + 1 :]
        return df  # In case all rows have the same timestamp
    else:
        # return all the data
        return df


def update_table(_df):
    """
    Updates the current measurements in the table
    """
    # create a deep copy as the df is significantly manipulated here
    df = _df.copy(deep=True)

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
    @app.callback(  # updates the data store
        Output("store-tec-data", "data"),
        [Input("interval-component", "n_intervals"), State("store-tec-data", "data")],
    )
    def update_store_data(n, existing_store_data_json):
        # Fetch data from the TEC interface
        df = tec_interface()._get_data()
        
            # check if the timestamp of the "new" data and most recent old data matches
            # in that case, do not append the data as we already have it
            # this happenes sometimes as TECInterface will only give new data every n second(s)
        global _last_data_timestamp
        
        new_timestamp = df.iloc[len(df) - 1]["timestamp"]
        if _last_data_timestamp == new_timestamp:
            return dash.no_update
        
        _last_data_timestamp = new_timestamp

        # if there is existing data, append to it. Otherwise, override it
        if existing_store_data_json:
            # convert existing data to df
            existing_df = get_data_from_store(existing_store_data_json, most_recent=False)

            # concat
            updated_df = pd.concat([existing_df, df])

            # convert back to json for storage
            updated_store_data_json = df_to_base64(updated_df)
        else:
            # convert new data to json for storage
            updated_store_data_json = df_to_base64(df)

        return updated_store_data_json

    @app.callback(  # handles the table and graphs
        [
            Output("tec-data-table", "data"),
            Output("tec-data-table", "columns"),
            Output("graph-object-temperature", "figure"),
            Output("graph-output-current", "figure"),
            Output("graph-output-voltage", "figure"),
        ],
        [Input("store-tec-data", "data"), State("btn-pause-graphs", "n_clicks")],
    )
    def update_components_from_store(store_data, n_clicks):
        
        # Update table
        df_recent = get_data_from_store(store_data, most_recent=True)

        _convert_timestamps(df_recent)

        format_timestamps(df_recent)
        
        

        table_data, table_columns = update_table(df_recent)

        # If graphs are not paused, update them as well
        if _is_graph_paused(n_clicks):
            return (
                table_data,
                table_columns,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        # Update graphs

        df_all = get_data_from_store(store_data, most_recent=False)

        _convert_timestamps(df_all)

        graph_object_temp = update_graph_object_temperature(df_all)
        graph_output_current = update_graph_max_current(df_all)
        graph_output_voltage = update_graph_max_voltage(df_all)

        return (
            table_data,
            table_columns,
            graph_object_temp,
            graph_output_current,
            graph_output_voltage,
        )

    @app.callback(
        Output("download-data-csv", "data"),
        [
            Input("btn-download-csv", "n_clicks"),
            State("checkboxes-download", "value"),
            State("store-tec-data", "data"),
        ],
        prevent_initial_call=True,
    )
    def download_all_data(n_clicks, selected_options, store_data):
        df = get_data_from_store(store_data, most_recent=False)

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
        tec_interface().disable_all_plates()
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

        tec_interface().set_temperature("top", top_temp)
        tec_interface().set_temperature("bottom", bottom_temp)

        tec_interface().enable_all_plates()
        return dash.no_update

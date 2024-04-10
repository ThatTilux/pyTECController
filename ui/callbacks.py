from datetime import datetime
from io import StringIO
import json
from time import sleep
from dash.dependencies import Output, Input, State
from dash import dcc
import pandas as pd
from tec_interface import TECInterface

_tec_interface: TECInterface = None


def tec_interface():
    global _tec_interface
    if _tec_interface is None:
        _tec_interface = TECInterface()
    return _tec_interface


def _convert_store_data_to_df(store_data):
    # Parse the JSON string into a Python dictionary
    data_dict = json.loads(store_data)

    # Extract the column names
    columns = data_dict["columns"]

    # Convert the multi-level index to a tuple index, which pandas can handle
    index = pd.MultiIndex.from_tuples(data_dict["index"], names=["Plate", "TEC_ID"])

    # Create the DataFrame using the data, column names, and multi-level index
    df = pd.DataFrame(data_dict["data"], index=index, columns=columns)

    return df


def same_timestamps(old_time, new_time):
    """
    Accepts an old and a new timestamp.
    The old timestamp has to be in the format 1712681273425
    The new timestamp has to be in the format 2024-04-09 16:47:48.683551
    Returns True if the timestamps match.
    """

    # Convert datetime object to a Unix timestamp in milliseconds
    new_ms = int(new_time.timestamp() * 1000)

    return new_ms == old_time


def get_data_from_store(store_data, most_recent=True):
    """Parses the data store and returns a dataframe with the data

    Args:
        store_data (string): json data from the data store
        most_recent (bool, optional): When set to true, only the most recent measurement is returned. When set to false, all recorded measurements are returned. Defaults to True.
    """
    if store_data is None:
        return None

    # convert json to df
    df = _convert_store_data_to_df(store_data)

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


# all callbacks inside this function
def register_callbacks(app):
    @app.callback(  # updates the data store
        Output("store-tec-data", "data"),
        [Input("interval-component", "n_intervals"), State("store-tec-data", "data")],
    )
    def update_store_data(n, existing_store_data_json):
        # Fetch data from the TEC interface
        df = tec_interface()._get_data()

        # if there is existing data, append to it. Otherwise, override it
        if existing_store_data_json:
            # convert existing data to df
            existing_df = _convert_store_data_to_df(existing_store_data_json)

            # check if the timestamp of the "new" data and most recent old data matches
            # in that case, do not append the data as we already have it
            # this happenes sometimes as TECInterface will only give new data every n second(s)
            if same_timestamps(
                old_time=existing_df.iloc[len(existing_df) - 1]["timestamp"],
                new_time=df.iloc[len(df) - 1]["timestamp"],
            ):
                return existing_store_data_json

            # concat
            updated_df = pd.concat([existing_df, df])

            # convert back to json for storage
            updated_store_data_json = updated_df.to_json(orient="split")
        else:
            # convert new data to json for storage
            updated_store_data_json = df.to_json(orient="split")

        return updated_store_data_json

    @app.callback(  # handles the table
        [Output("tec-data-table", "data"), Output("tec-data-table", "columns")],
        [Input("store-tec-data", "data")],
    )
    def update_table_from_store(store_data):
        df = get_data_from_store(store_data, most_recent=True)

        # Preparing data for the DataTable
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict("records")
        return data, columns

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

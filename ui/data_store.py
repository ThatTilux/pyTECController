"""
Handles the data store. Dataframes are converted to base64 using parquet and then stored.
"""

import base64
import io
import dash

import pandas as pd

# timestamp of the last data pulled
_last_data_timestamp = None


def df_to_base64(df):
    """
    Converts a dataframe to base64 for storage
    """
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=True)  # includes index
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

def get_most_recent(df):
    """
    Will return the last x rows from a dataframe that all have the same timestamp
    """
    # get the most recent timestamp from the last row and return all rows with that one
    last_index = len(df) - 1
    most_recent_timestamp = df.iloc[last_index]["timestamp"]

    # Iterate backwards until a different timestamp is found
    for i in range(last_index, -1, -1):
        if df.iloc[i]["timestamp"] != most_recent_timestamp:
            # Slice from the next index to the end to get all rows with the most recent timestamp
            return df.iloc[i + 1 :]
    return df  # In case all rows have the same timestamp
    


def get_data_from_store(store_data):
    """Parses the data store and returns a dataframe with the data

    Args:
        store_data (string): base64 data from the data store
    """
    if store_data is None:
        return None

    # convert json to df
    df = base64_to_df(store_data)

    if df.empty:
        return df

    # return all the data
    return df


def update_store(new_data, existing_data):
    # check if the timestamp of the "new" data and most recent old data matches
    # in that case, do not append the data as we already have it
    # this happenes sometimes as TECInterface will only give new data every n second(s)
    global _last_data_timestamp

    new_timestamp = new_data.iloc[len(new_data) - 1]["timestamp"]
    if _last_data_timestamp == new_timestamp:
        return dash.no_update

    _last_data_timestamp = new_timestamp

    # if there is existing data, append to it. Otherwise, override it
    if existing_data:
        # convert existing data to df
        existing_df = get_data_from_store(existing_data)

        # concat
        updated_df = pd.concat([existing_df, new_data])

        # convert back to json for storage
        updated_store_data_json = df_to_base64(updated_df)
    else:
        # convert new data to json for storage
        updated_store_data_json = df_to_base64(new_data)

    return updated_store_data_json

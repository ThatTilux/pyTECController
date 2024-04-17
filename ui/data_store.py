"""
Handles the data store. Dataframes are converted to base64 using parquet and then stored.
"""

import base64
import io
import dash
import redis

import pandas as pd

from app.serial_ports import NUM_TECS

# timestamp of the last data pulled
_last_data_timestamp = None

# redis connection for storing data
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# stores current data
REDIS_KEY_STORE = "tec-data-store"

# stores data that was too old for the above storage
REDIS_KEY_STORE_ALL = "tec-data-store-all"

# channel for recovered data
REDIS_KEY_PREVIOUS_DATA = "tec-data-store-previous"

# channel for notifying the ui in case of dummy mode
REDIS_KEY_DUMMY_MODE = "dummy-mode"

pubsub_dummy_mode = r.pubsub()
pubsub_dummy_mode.subscribe(REDIS_KEY_DUMMY_MODE)

# this is the maximum number of rows that will be stored
# everything above this will be moved to the STORE_ALL channel
MAX_ROWS_STORAGE = 8000

# when the above limit of rows above is exceeded, this many rows will be moved
REMOVE_ROWS_COUNT = 1504

# do not disrupt data
assert REMOVE_ROWS_COUNT % NUM_TECS == 0


def df_to_base64(df):
    """
    Converts a dataframe to base64 with parquet for storage
    """
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=True)  # includes index
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded


def base64_to_df(encoded):
    """
    Converts a base64 with parquet encoded dataframe back to a dataframe
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


def get_data_from_store(channel=REDIS_KEY_STORE):
    """
    Gets the data from the store and returns a dataframe with the data
    """

    # get data from storage channel
    store_data = r.get(channel)

    if store_data is None:
        return None

    # convert encoded data to df
    df = base64_to_df(store_data)

    # return all the data
    return df

def get_recovered_data():
    """
    Gets the data that was saved from the previous session.
    """
    return get_data_from_store(REDIS_KEY_PREVIOUS_DATA)


def get_data_for_download():
    """
    Stichtes the data from both channels together
    """
    df_1 = get_data_from_store(channel=REDIS_KEY_STORE_ALL)
    df_2 = get_data_from_store(channel=REDIS_KEY_STORE)

    df = pd.concat([df_1, df_2])

    return df


def update_store(new_data, channel=REDIS_KEY_STORE):
    """
    Appends new data to the data store.
    """
    global _last_data_timestamp

    # check if the timestamp of the "new" data and most recent old data matches
    # in that case, do not append the data as we already have it
    # this may happen sometimes as TECInterface will only give new data every n second(s)
    if channel == REDIS_KEY_STORE:
        new_timestamp = new_data.iloc[len(new_data) - 1]["timestamp"]

        if _last_data_timestamp == new_timestamp:
            return dash.no_update

        _last_data_timestamp = new_timestamp

    # get the existing data
    existing_data = get_data_from_store(channel)

    # if there is existing data, append to it. Otherwise, override it
    if existing_data is not None:
        # concat
        updated_df = pd.concat([existing_data, new_data])

        # check if the data is too large
        if channel == REDIS_KEY_STORE and len(updated_df) > MAX_ROWS_STORAGE:
            # move some data to the other channel
            updated_df = transfer_rows(updated_df)

        # convert back for storage
        updated_store_data = df_to_base64(updated_df)

    else:
        # convert new data for storage
        updated_store_data = df_to_base64(new_data)

    # update the data store
    r.set(channel, updated_store_data)


def transfer_rows(df):
    """
    Removes rows from the dataframe and stores them in the other channel.
    """
    # create new df
    new_df = df.iloc[:REMOVE_ROWS_COUNT].copy()

    # remove the rows
    df = df.iloc[REMOVE_ROWS_COUNT:]

    # update the store
    update_store(channel=REDIS_KEY_STORE_ALL, new_data=new_df)

    return df

def detect_dummy():
    """
    Listens to a pubsub channel to check if dummy mode was activated
    """
    global pubsub_dummy_mode
    message = pubsub_dummy_mode.get_message()
    
    # if the backend posted a message to the channel, dummy mode is activated
    if message:
        return True
    return False

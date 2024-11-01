"""
This class acts as an interface between the app (SystemTECController.py) and the UI
"""

# Make sure the user set up the serial_ports file
try:
    from app.serial_ports import PORTS
except ImportError as e:
    for i in range(3):
        print(
            f"[ERROR] Please create the serial_ports.py file. See README for details."
        )
    input("Press Enter to continue....")
    exit()

import redis
from app.system_tec_controller import SystemTECController
from time import sleep, time
import pandas as pd

from mecom.exceptions import ResponseException
from redis_keys import (
    REDIS_HOST,
    REDIS_KEY_STORE,
    REDIS_KEY_STORE_ALL,
    REDIS_KEY_DUMMY_MODE,
    REDIS_KEY_PREVIOUS_DATA,
    REDIS_KEY_RECONNECTING,
    REDIS_PORT,
)
from ui.callbacks.graphs_tables import _convert_timestamps
from ui.components.graphs import format_timestamps
from ui.data_store import get_data_both_channels, get_data_from_store, update_store


class TECInterface:
    # Use existing data if last update was within this duration (in seconds)
    _UPDATE_THRESHOLD = 0.3

    def __init__(self):
        self.system_controller = SystemTECController(
            ports_top=[PORTS["TOP_1"], PORTS["TOP_2"]],
            ports_bottom=[PORTS["BOTTOM_1"], PORTS["BOTTOM_2"]],
        )
        # all measurements from all TECs
        self._data = pd.DataFrame()

        # timestamp when data was last updated
        self._data_time = -1

    def get_data(self):
        """
        Returns data from all connected TECs as a dataframe.
        May return previous data if called too frequently.
        """
        # get fresh data if UPDATE_THRESHOLD is exceeded, otherwise provide existing data
        if time() - self._data_time >= self._UPDATE_THRESHOLD:
            self._data = self.system_controller.get_data()
            self._data_time = time()
            return self._data
        else:
            return self._data

    def set_temperature(self, plate, temperature):
        """
        Sets the target temperature for the TECs of one of the two plates.
        Only to be used in Temperature Control mode.
        """
        self.system_controller.set_temp(plate, temperature)

    def set_target(self, plate, target):
        """
        Sets the target temperature for the TECs of one of the two plates.
        Only to be used in static current/voltage mode.
        """
        self.system_controller.set_target(plate, target)

    def enable_plate(self, plate):
        """
        Enables the TECs for one of the two plates.
        """
        self.system_controller.enable(plate)

    def disable_plate(self, plate):
        """
        Disables the TECs for one of the two plates.
        """
        self.system_controller.disable(plate)

    def disable_all_plates(self):
        """
        Disables the TECs for both plates.
        """
        self.system_controller.disable_all()

    def enable_all_plates(self):
        """
        Enables the TECs for both plates.
        """
        self.system_controller.enable_all()

    def handle_message(self, message):
        """
        Handles an incoming message from the UI.
        Format: "command$$value1$$value2$$.."
        """
        splitted = message["data"].split("$$")
        command = splitted[0]
        match command:
            case "SET_TEMP":
                plate = splitted[1]
                temp = float(splitted[2])
                self.set_target(plate, temp)
            case "DISABLE_ALL":
                self.disable_all_plates()
            case "ENABLE_ALL":
                self.enable_all_plates()


class DummyInterface:
    """
    Dummy version of the TECInterface.
    Will provide pre-recorded data.
    """

    def __init__(self, dummy_csv_path):
        self.df = pd.read_csv(dummy_csv_path)
        # set multi level index
        self.df.set_index(["Plate", "TEC"], inplace=True)
        self.counter = 0

    def get_data(self):
        """
        Returns the next 8 rows (=> 1 measurement) of the pre-recorded data.
        """
        start = self.counter * 8
        self.counter = self.counter + 1

        if start + 8 > len(self.df):
            return pd.DataFrame()

        return self.df[start : start + 8]

    def handle_message(self, message):
        """
        Does not handle UI Commands.
        """
        pass


# this is the data aquisition program
if __name__ == "__main__":

    # connect to the redis storage
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

    # save all previous data
    r.delete(REDIS_KEY_PREVIOUS_DATA)
    previous_data = get_data_both_channels()
    update_store(previous_data, REDIS_KEY_PREVIOUS_DATA)

    # clean up the data channels
    r.delete(REDIS_KEY_STORE)
    r.delete(REDIS_KEY_STORE_ALL)
    r.delete(REDIS_KEY_DUMMY_MODE)
    r.delete(REDIS_KEY_RECONNECTING)

    pubsub_dummy_mode = r.pubsub()
    pubsub_dummy_mode.subscribe(REDIS_KEY_DUMMY_MODE)
    pubsub_dummy_mode.subscribe(REDIS_KEY_RECONNECTING)

    # listen to ui commands channel
    pubsub = r.pubsub()
    pubsub.subscribe("ui_commands")

    # try to connect to the TECs
    # use dummy data if connection unsuccessful
    dummy = False
    # keep track if all TECs are online right now
    tecs_online = True
    try:
        tec_interface = TECInterface()
    except Exception as e:
        print(e)
        tec_interface = DummyInterface("app/dummy_data/dummy.csv")
        dummy = True

    # pull data until program is stopped
    while True:
        time_start = time()  # in seconds

        # listen to any UI commands
        message = pubsub.get_message()
        while message and message["type"] == "message":
            tec_interface.handle_message(message)
            message = pubsub.get_message()

        # get and store fresh data
        try:
            data = tec_interface.get_data()  # ResponseTimeout can only occur here
            update_store(data)

            # if tecs were offline before, signal that all are connected again
            if not tecs_online:
                r.publish(REDIS_KEY_RECONNECTING, f"ConnectionReestablished$${time()}")
                tecs_online = True

            # print the current data for debugging
            df = get_data_from_store()
            _convert_timestamps(df)
            format_timestamps(df)
            print(df)
        except ResponseException as ex:
            # some TECs have encountered an error and are restarting.
            # instead of sending data, send the signal that an error has occured
            r.publish(REDIS_KEY_RECONNECTING, f"Reconnecting$${time()}")
            tecs_online = False

        # Print dummy-info
        if dummy:
            print("TECs not connected. Using dummy data.")
            # inform the UI of dummy mode
            r.publish(REDIS_KEY_DUMMY_MODE, f"True$${time()}")

        # sleep to achieve a polling rate of 1Hz
        sleep_time = 1 - (time() - time_start)
        print(f"Sleeping for {sleep_time}s...")
        if sleep_time > 0:
            sleep(sleep_time)
        else:
            print(
                "[WARNING]: Sampling rate fell below 1Hz. Lowering MAX_ROWS_STORAGE in ui.data_store might help."
            )

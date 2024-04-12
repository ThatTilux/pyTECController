"""
This class acts as an interface between the app (SystemTECController.py) and the UI
"""

import base64
import io

import redis
from app.system_tec_controller import SystemTECController
from app.serial_ports import PORTS  
from time import sleep, time
import pandas as pd

from ui.callbacks import _convert_timestamps
from ui.components.graphs import format_timestamps
from ui.data_store import get_data_from_store, update_store

class TECInterface:
    # Use existing data if last update was within this duration (in seconds)
    _UPDATE_THRESHOLD = .3
    
    
    def __init__(self):
        self.system_controller = SystemTECController(
            ports_top=[PORTS["TOP_1"], PORTS["TOP_2"]],
            ports_bottom=[PORTS["BOTTOM_1"], PORTS["BOTTOM_2"]],
        )
        # all measurements from all TECs
        self._data = pd.DataFrame()
        
        # timestamp when data was last updated
        self._data_time = -1
        
            
    def _get_data(self):
        # get fresh data if UPDATE_THRESHOLD is exceeded, otherwise provide existing data
        if time() - self._data_time >= self._UPDATE_THRESHOLD:
            self._data = self.system_controller.get_data()
            self._data_time = time()
            return self._data
        else:
            return self._data

    def set_temperature(self, plate, temperature):
        self.system_controller.set_temp(plate, temperature)

    def enable_plate(self, plate):
        self.system_controller.enable(plate)

    def disable_plate(self, plate):
        self.system_controller.disable(plate)

    def disable_all_plates(self):
        self.system_controller.disable_all()

    def enable_all_plates(self):
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
                self.set_temperature(plate, temp)
            case "DISABLE_ALL":
                self.disable_all_plates()
            case "ENABLE_ALL":
                self.enable_all_plates()
            
                    






# this is the data aquisition program
if __name__ == "__main__":
    


    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    REDIS_KEY = "tec-data-store"
    r.delete(REDIS_KEY)
    
    # listen to ui commands channel
    pubsub = r.pubsub()
    pubsub.subscribe("ui_commands")

    _last_data_timestamp = None
    
    tec_interface = TECInterface()
    
    
    while True:
        time_start = time() # in seconds
        
        # listen to any commands
        message = pubsub.get_message()        
        while message and message["type"] == "message":
            tec_interface.handle_message(message)
            message = pubsub.get_message()       
            
        # get and store data
        data = tec_interface._get_data()
        update_store(data)
        
        # just for testing
        df = get_data_from_store()
        _convert_timestamps(df)
        format_timestamps(df)
        print(df)
        
        # sleep to get measurements every second
        sleep_time = 1 - (time() - time_start) 
        print(f"{sleep_time}s")
        if sleep_time > 0:
            sleep(sleep_time)
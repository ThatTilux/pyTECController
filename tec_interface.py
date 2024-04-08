"""
This class acts as an interface between the app (SystemTECController.py) and the UI
"""

from app.SystemTECController import SystemTECController
from app.serial_ports import PORTS  
from time import time

class TECInterface:
    # Use existing data if last update was within this duration (in seconds)
    _UPDATE_THRESHOLD = 1
    
    
    def __init__(self):
        self.system_controller = SystemTECController(
            ports_top=[PORTS["TOP_1"], PORTS["TOP_2"]],
            ports_bottom=[PORTS["BOTTOM_1"], PORTS["BOTTOM_2"]],
        )
        # all measurements from all TECs
        self._data = {}
        
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



    # TODO: methods for getting the exact data the UI needs


# temp example code

if __name__ == "__main__":
    tec_interface = TECInterface()
    
    print(tec_interface._get_data())
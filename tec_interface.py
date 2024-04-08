"""
This class acts as an interface between the app (SystemTECController.py) and the UI
"""

from app.SystemTECController import SystemTECController
from app.serial_ports import PORTS  

class TECInterface:
    def __init__(self):
        self.system_controller = SystemTECController(
            ports_top=[PORTS["TOP_1"], PORTS["TOP_2"]],
            ports_bottom=[PORTS["BOTTOM_1"], PORTS["BOTTOM_2"]],
        )

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


from app.plate_tec_controller import PlateTECController
from app.serial_ports import PORTS
import pandas as pd
from datetime import datetime


class SystemTECController:
    """
    This class controls the entire contraption, i.e. both plates.
    """

    def __init__(self, ports_top=None, ports_bottom=None):
        top = PlateTECController(label="top", ports=ports_top)
        bottom = PlateTECController(label="bottom", ports=ports_bottom)
        self.controllers = {"top": top, "bottom": bottom}

    def set_temp(self, plate, temp):
        """Sets the temperature for a plate.

        Args:
            plate (string): top or bottom
            temp (float): desired temperature
        """
        assert plate in ["top", "bottom"]
        self.controllers[plate].set_temp_all(temp)

    def enable(self, plate):
        """Enables all TECs on a plate.

        Args:
            plate (string): top or bottom
        """
        assert plate in ["top", "bottom"]
        self.controllers[plate].enable_all()

    def disable(self, plate):
        """Disables all TECs on a plate.

        Args:
            plate (string): top or bottom
        """
        assert plate in ["top", "bottom"]
        self.controllers[plate].disable_all()

    def disable_all(self):
        """
        Disables both plates
        """
        self.disable("top")
        self.disable("bottom")

    def enable_all(self):
        """
        Enables both plates
        """
        self.enable("top")
        self.enable("bottom")

    def get_data(self):
        """
        Returns a dataframe with all the data for all TECs.
        """
        data = {}
        for label in self.controllers:
            controller = self.controllers[label]
            data[label] = controller.get_data()
            
        frames = []
        for plate, plate_data in data.items():
            for tec_id, tec_data in plate_data.items():
                df = pd.DataFrame([tec_data])
                df['TEC'] = tec_id
                df['Plate'] = plate
                frames.append(df)

        # Concatenate all small DataFrames and set multi-index
        df = pd.concat(frames).set_index(['Plate', 'TEC']).sort_index()
        
        # add timestamps
        df["timestamp"] = datetime.now()
            
        return df

    def get_temps_avg(self, plate):
        assert plate in ["top", "bottom"]


# example code
if __name__ == "__main__":
    mc = SystemTECController(
        ports_top=[PORTS["TOP_1"], PORTS["TOP_2"]],
        ports_bottom=[PORTS["BOTTOM_1"], PORTS["BOTTOM_2"]],
    )

    mc.disable_all()

    # set this to False incase the only purpose is to stop all TECs
    cont = False

    if not cont:
        exit()

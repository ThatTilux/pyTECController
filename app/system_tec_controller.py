from app.plate_tec_controller import PlateTECController
from app.serial_ports import PORTS
import pandas as pd
from datetime import datetime

from app.tec_controller import TECController


class SystemTECController:
    """
    This class controls the entire contraption, i.e. both plates.
    """

    def __init__(self, ports_top=None, ports_bottom=None, ports_external=None):
        top = PlateTECController(label="top", ports=ports_top)
        bottom = PlateTECController(label="bottom", ports=ports_bottom)
        self.controllers = {"top": top, "bottom": bottom}
        
        # set up external sensors (read only)
        if ports_external:
            self.external_tecs = self._connect_external_tecs(ports_external)

    def set_temp(self, plate, temp):
        """Sets the temperature for a plate.
        Only to be used in Temperature Control mode.

        Args:
            plate (string): top or bottom
            temp (float): desired temperature
        """
        assert plate in ["top", "bottom"]
        self.controllers[plate].set_temp_all(temp)
        
    def set_target(self, plate, target):
        """Sets the temperature for a plate.
        Only to be used in static current/voltage mode.

        Args:
            plate (string): top or bottom
            temp (float): desired temperature
        """
        assert plate in ["top", "bottom"]
        self.controllers[plate].set_target(target)

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
        # Get data of TECs
        data = {}
        for label, controller in self.controllers.items():
            data[label] = controller.get_data()
            
        frames = []
        for plate, plate_data in data.items():
            for tec_id, tec_data in plate_data.items():
                df = pd.DataFrame([tec_data])
                df['TEC'] = tec_id
                df['Plate'] = plate
                frames.append(df)
                
        # add data of external TECs
        if hasattr(self, "external_tecs"):
            data_ext = {}
            for i, (label, tec) in enumerate(self.external_tecs.items()):
                data_ext[i] = tec.get_data()
            
            for tec_id, tec_data in data_ext.items():
                df = pd.DataFrame([tec_data])
                df['TEC'] = tec_id
                df['Plate'] = "external"
                frames.append(df)    

        # Concatenate all small DataFrames and set multi-index
        df = pd.concat(frames).set_index(['Plate', 'TEC']).sort_index()
        
        # sort the df by 'Plate' reverse alphabetical order and then by 'TEC' ascendingly
        df = df.sort_values(by=['Plate', 'TEC'], ascending=[False, True])
        
        # add power column
        df["output power"] = (df["output current"] * df["output voltage"]).abs()
        
        # add timestamps (ms since last epoch)
        df["timestamp"] = int(datetime.now().timestamp() * 1000) 
            
        return df

    def get_temps_avg(self, plate):
        assert plate in ["top", "bottom"]
        
    def _connect_external_tecs(self, ports):
        controllers = {}
        for i, port in enumerate(ports):
            for channel in range(1, 3):
                controllers[f"EXT_{i}_CH_{channel}"] = TECController(channel=channel, port=port)
        return controllers


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

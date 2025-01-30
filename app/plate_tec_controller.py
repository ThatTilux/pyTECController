import logging
from time import sleep
from app.tec_controller import TECController
from app.serial_ports import PORTS


class PlateTECController:
    """
    Controls multiple TECs that all heat/cool the same plate
    """

    def __init__(self, label, ports=None):
        """
        Args:
            label (string): top or bottom
            ports ([string]): ports to establish connection to. Defaults to None.
        """
        self.ports = ports
        self.label = label
        self.tec_controllers = self._connect_tecs(self.ports)
        self.target = None

    def _connect_tecs(self, ports):
        controllers = {}
        id_counter = 0
        for port in ports:
            # Use both channels
            controllers[id_counter] = TECController(channel=1, port=port)
            # set parallel mode for the first channel
            controllers[id_counter].set_parallel_mode()
            id_counter += 1
            controllers[id_counter] = TECController(channel=2, port=port)
            id_counter += 1
        return controllers

    def get_data(self):
        """
        Returns the data for all managed TECs
        """
        data = {}
        for tec_id in self.tec_controllers:
            tec = self.tec_controllers[tec_id]
            data[tec_id] = tec.get_data()

        return data

    def print_data(self, tec_id):
        """
        Prints the data of one TEC
        """
        print(self.tec_controllers[tec_id].get_data())

    def print_data_all(self):
        """
        Prints the data for all TECs.
        """
        print(f"===plate {self.label}===")
        for tec in self.tec_controllers.values():
            print(tec.get_data())

    def set_temp_all(self, temp):
        for tec in self.tec_controllers.values():
            tec.set_temp(temp)

    def set_current_all(self, current):
        for tec in self.tec_controllers.values():
            tec.set_current(current)

    def enable_all(self):
        for tec in self.tec_controllers.values():
            tec.enable()

    def disable_all(self):
        for tec in self.tec_controllers.values():
            tec.disable()

    def set_target(self, target):
        """
        Sets the target temperature for the plate.
        Only to be used in static current/voltage mode.
        """
        assert type(target) is float
        self.target = target
        # only for display
        self.set_temp_all(target)


# temporary test function
def _print_temp(mc):
    """TEST
    prints the temps and loop info in the console
    """
    temps = []
    loop = "Not active"
    for tec in mc.tec_controllers.values():
        data = tec.get_data()
        temps.append(round(data["object temperature"][0], 2))
        status = data["loop status"][0]
        if status == 1:
            loop = "Not stable"
        elif status == 2 and loop != "Not stable":
            loop = "Stable"
    avg = round(sum(temps) / len(temps), 2)

    print(
        f"Temps for {mc.label}: {temps[0]}, {temps[1]}, {temps[2]}, {temps[3]}, AVG: {avg}, Temp Regulation: {loop}"
    )


# some example code
if __name__ == "__main__":
    # start logging
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s"
    )

    # initialize both plates
    mc_top = PlateTECController(label="top", ports=[PORTS["TOP_1"], PORTS["TOP_2"]])
    mc_bottom = PlateTECController(
        label="bottom", ports=[PORTS["BOTTOM_1"], PORTS["BOTTOM_2"]]
    )

    mc_top.disable_all()
    mc_bottom.disable_all()

    cont = False

    if not cont:
        exit()

    # print data
    # mc_top.print_data_all()
    # mc_bottom.print_data_all()

    # set temp
    mc_top.set_temp_all(35.0)

    mc_top.enable_all()

    for i in range(0, 1000):
        _print_temp(mc_top)
        sleep(1)

    mc_top.disable_all()

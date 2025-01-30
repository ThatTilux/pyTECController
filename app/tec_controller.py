"""
Class for handling one TEC via one channel of a TEC-1161 board.
"""

import base64
import io
import logging
from time import sleep
from mecom import MeComSerial, ResponseException, WrongChecksum
import pandas as pd
import redis
from serial.serialutil import SerialException
from app.queries import COMMAND_TABLE, DEFAULT_QUERIES
from app.serial_ports import PORTS
from app.param_values import PARAM_VALUES


class TECController(object):
    """
    Controlling one TEC device via serial.
    """

    # class-level dictionary to hold all serial session instances indexed by port
    # (we need 2 instances of this class per port but only 1 session)
    _sessions = {}

    # number of successive times that the get_data function timed out
    _num_timeout_get_data = 0

    # allow the get_data function to timeout this many times before closing the connection
    _num_timeout_limit = 60

    def _tearDown(self):
        self.session().stop()

    def __init__(
        self,
        port=None,
        scan_timeout=30,
        channel=1,
        queries=DEFAULT_QUERIES,
        *args,
        **kwars,
    ):
        assert channel in (1, 2)
        self.channel = channel
        self.port = port
        self.scan_timeout = scan_timeout
        self.queries = queries

        self._connect()

        self._set_params()

        # we want to run in temperature control mode
        self.set_temperature_control_mode()

    def _connect(self):
        # open session or use existing one
        if self.port in TECController._sessions:
            self._session = TECController._sessions[self.port]
        else:
            self._session = MeComSerial(serialport=self.port)
            TECController._sessions[self.port] = self._session

        # get device address
        self.address = self._session.identify()
        logging.info(
            "connected to address {} with serialport {} and channel {}".format(
                self.address, self.port, self.channel
            )
        )

    def session(self):
        if self._session is None:
            self._connect()
        return self._session

    def get_data(self):
        data = {}
        for description in self.queries:
            id, _ = COMMAND_TABLE[description]
            try:

                value = self.session().get_parameter(
                    parameter_id=id,
                    address=self.address,
                    parameter_instance=self.channel,
                )
                data.update({description: value})
                self._num_timeout_get_data = 0

            except ResponseException as ex:
                # TEC is offline and may currently be restarting.
                # Instead of stopping the session, throw exception to be handled.
                # Only do this n times
                self._num_timeout_get_data += 1

                if self._num_timeout_get_data >= self._num_timeout_limit:
                    # close connection
                    self.session().stop()
                    self._session = None
                    raise RuntimeError

                # throw exception to be handled
                raise ex

            except WrongChecksum as ex:
                self.session().stop()
                self._session = None
        return data

    def _set_params(self):
        """
        Sets values for certain parameters to prevent damage to components and get optimal behavior.
        """
        for description in PARAM_VALUES:
            param_id, unit, value = PARAM_VALUES[description]
            try:
                # Make sure every param is in COMMAND_TABLE
                assert param_id, unit == COMMAND_TABLE[description]

                self.session().set_parameter(
                    parameter_id=param_id,
                    value=value,
                    address=self.address,
                    parameter_instance=self.channel,
                )
            except (ResponseException, WrongChecksum) as ex:
                logging.error("ERROR in setting parameter limits. Aborting.")
                self.session().stop()
                self._session = None
                
        # if this is channel 1, set the delay till restart
        if self.channel == 1:
            self.set_delay_till_restart(5.0) # 5s

    def set_static_mode(self):
        """
        Enables the mode "Static Current/Voltage"
        """
        return self._set_input_selection(0)

    def set_temperature_control_mode(self):
        """
        Enables the mode "Temperature Controller"
        """
        return self._set_input_selection(2)

    def set_delay_till_restart(self, value):
        """
        Sets the delay for automatic restart after error (in seconds).
        0 = disabled.
        """
        assert type(value) is float
        logging.info(
            "set delay till restart to {} for channel {}".format(value, self.channel)
        )
        return self.session().set_parameter(
            parameter_name="Delay till Restart",
            value=value,
            address=self.address,
            parameter_instance=self.channel,
        )

    def _set_input_selection(self, value):
        """
        Changes the input selection
        0: Static Current/Voltage
        1: Live Current/Voltage
        2: Temperature Control
        """
        value = int(value)
        assert value in [0, 1, 2]

        logging.info(
            "set input selection to {} for channel {}".format(value, self.channel)
        )
        return self.session().set_parameter(
            parameter_name="Input Selection",
            value=value,
            address=self.address,
            parameter_instance=self.channel,
        )

    def set_parallel_mode(self):
        """
        Sets the mode of operation to parallel with individual load.
        """
        return self._set_general_operating_mode(1)

    def set_individual_mode(self):
        """
        Sets the mode of operation to individual.
        """
        return self._set_general_operating_mode(0)

    def _set_general_operating_mode(self, value):
        """
        Sets the general operating mode.
        0: Single (Independent)
        1: Parallel (CH1 → CH2); Individual Loads
        2: Parallel: (CH1 → CH2); Common Load
        """
        value = int(value)
        assert value in [0, 1, 2]

        logging.info(
            "set general operating mode to {} for channel {}".format(
                value, self.channel
            )
        )
        return self.session().set_parameter(
            parameter_name="General Operating Mode",
            value=value,
            address=self.address,
            parameter_instance=self.channel,
        )

    def set_temp(self, value):
        """
        Set object temperature of channel to desired value.
        :param value: float
        :param channel: int
        :return:
        """
        # assertion to explicitly enter floats
        assert type(value) is float
        logging.info(
            "set object temperature for channel {} to {} C".format(self.channel, value)
        )
        return self.session().set_parameter(
            parameter_id=3000,
            value=value,
            address=self.address,
            parameter_instance=self.channel,
        )

    def set_current(self, value):
        """
        Set the current when in mode static current/voltage
        """
        assert type(value) is float
        logging.info(
            "set static current for channel {} to {} C".format(self.channel, value)
        )
        return self.session().set_parameter(
            parameter_id=2020,
            value=value,
            address=self.address,
            parameter_instance=self.channel,
        )

    def _set_enable(self, enable=True):
        """
        Enable or disable control loop
        :param enable: bool
        :param channel: int
        :return:
        """
        value, description = (1, "on") if enable else (0, "off")
        logging.info("set loop for channel {} to {}".format(self.channel, description))
        return self.session().set_parameter(
            value=value,
            parameter_name="Status",
            address=self.address,
            parameter_instance=self.channel,
        )

    def enable(self):
        return self._set_enable(True)

    def disable(self):
        return self._set_enable(False)


def test_connection():
    """
    Tests which of the specified ports can be reached.
    """
    for label in PORTS:
        port = PORTS[label]
        try:
            mc = TECController(port=port)
            mc._tearDown()
            print(f"Port {label} is online")
        except SerialException as ex:
            print(f"Port {label} is offline")


# example code
if __name__ == "__main__":
    pass

    # test_connection()

    # mc1 = MeerstetterTEC(port=PORTS["TOP_1"], channel=1)
    # mc2 = MeerstetterTEC(port=PORTS["TOP_1"], channel=2)

    # print(mc1.get_data())
    # print(mc2.get_data())

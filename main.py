"""
Class for handling both channels of one TEC-1161 board 
"""

import logging
from meerstetter_tec import MeerstetterTEC
from serial_ports import PORT_TOP_1, PORT_TOP_2, PORT_BOTTOM_1, PORT_BOTTOM_2


if __name__ == '__main__':
    # start logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s:%(module)s:%(levelname)s:%(message)s")

    # initialize controller
    mc1 = MeerstetterTEC(channel=1, port=PORT_TOP_1)
    mc2 = MeerstetterTEC(channel=2, port=PORT_TOP_1)

    # get the values from DEFAULT_QUERIES
    print(mc1.get_data())
    print(mc2.get_data())
    
    # set the temperature to 30
    mc1.set_temp(30.0)
    
    # activate
    mc1.enable()
    
    # get the values
    # for i in range(0, 10):
    #     print(mc.get_data())
    #     # sleep 1 sec
    #     sleep(1)
    
    # disable again
    mc1.disable()
    
    
    
    


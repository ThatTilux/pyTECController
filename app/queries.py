# default queries from command table below
# these are all the parameters that are pulled from each TEC
DEFAULT_QUERIES = [
    "loop status",
    "object temperature",
    "target object temperature",
    "output current",
    "output voltage",
]


# syntax
# { display_name: [parameter_id, unit], }
COMMAND_TABLE = {
    "loop status": [1200, ""],
    "object temperature": [1000, "degC"],
    "target object temperature": [1010, "degC"],
    "output current": [1020, "A"],
    "output voltage": [1021, "V"],
    "sink temperature": [1001, "degC"],
    "ramp temperature": [1011, "degC"],
    "current limitation": [2030, "A"],  # max current that will be provided
    "voltage limitation": [2031, "V"],  # max voltage that will be provided
    "input selection" :[2000, ""], # 0 for static current/voltage, 2 for temperature controller
    "set current": [2020, "A"], # sets the current when in mode static current/voltage
    "kp": [3010, ""], # sets the current when in mode static current/voltage
    "ti": [3011, ""], # sets the current when in mode static current/voltage
    "td": [3012, ""], # sets the current when in mode static current/voltage
    "lower error threshold": [4010, "degC"], #min temp
    "upper error threshold": [4011, "degC"], #max temp
    "td": [3012, ""], #max temp
    "source selection": [6300, ""], # which temperature sensor is used for temperature measurement
    "delay till restart": [6310, ""], # auto-reset delay on error
}
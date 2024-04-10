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
}
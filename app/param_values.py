"""
Defines some default parameters to prevent damage to components and optimal behavior.
"""

# syntax
# { display_name: [parameter_id, unit, limit]}
PARAM_VALUES = {
    "current limitation": [2030, "A", 9],  # max current provided
    "voltage limitation": [2031, "V", 10],  # max voltage provided
    "lower error threshold": [
        4010,
        "degC",
        0,
    ],  # min temperature (will shut off when below)
    "upper error threshold": [
        4011,
        "degC",
        75,
    ],  # max temperature (will shut off when above)
    "kp": [3010, "", 90],
    "ti": [3011, "", 0],
    "td": [3012, "", 0],
    "source selection": [6300, "", 0], # always use CH1 temperature sensor
    # delay till restart is set manually in the plate controller since it only applies to CH1
}

TEMP_INPUT_LIMITS = {  # limits for the temperature input fields in the UI in °C
    "max": (PARAM_VALUES["upper error threshold"][2] - 7),
    "min": (PARAM_VALUES["lower error threshold"][2] + 7),
    "step": 0.01,  # allow 0.01 precision, not more
}

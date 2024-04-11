"""
Defines parameter limits to prevent damage to components.
"""

# syntax
# { display_name: [parameter_id, unit, limit]}
PARAM_LIMITS = {
    "current limitation": [2030, "A", 9],
    "voltage limitation": [2031, "V", 10],
}

TEMP_INPUT_LIMITS = { # limits for the temperature input fields in the UI in °C
    "max": 65,
    "min": 0,
    "step": 0.01 # allow 0.01 precision, not more
}

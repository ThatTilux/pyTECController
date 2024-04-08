"""
Defines parameter limits to prevent damage to components.
"""

# syntax
# { display_name: [parameter_id, unit, limit]}
PARAM_LIMITS = {
    "current limitation": [2030, "A", 9],
    "voltage limitation": [2031, "V", 10],
}
# TODO: temperature limitation (fixed to 68C atm)

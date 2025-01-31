"""
Defines some default parameters for the TEC controllers to prevent damage to components and optimal behavior.
Do not touch these unless you are aware of the consequences.
"""

# Number of Thermoelectric Coolers (TECs)
NUM_TECS = 8

# Number of external TECs
num_external_tecs = 0 # adjusted at runtime based on UI selection

def get_external_tec_labels():
    # format is EXTERNAL_{n//2} ({'CH1' if n%2==0 else 'CH2'})
    labels = [get_external_tec_label_from_id(i) for i in range(num_external_tecs)]

    return labels

def get_external_tec_label_from_id(tec_id):
    return f"EXTERNAL_{tec_id//2} ({'CH1' if tec_id%2==0 else 'CH2'})"

def get_external_id_from_label(label):
    # from format EXTERNAL_{n//2} ({'CH1' if n%2==0 else 'CH2'})
    tec_id = int(label.split('_')[1].split()[0])
    if 'CH2' in label:
        tec_id = tec_id*2 + 1
    else:
        tec_id = tec_id*2
    return tec_id

# syntax
# { display_name: [parameter_id, unit, limit]}
PARAM_VALUES = {
    "current limitation": [2030, "A", 9],  # max current provided
    "voltage limitation": [2031, "V", 10],  # max voltage provided 
    "lower error threshold": [
        4010,
        "degC",
        -7, 
    ],  # min temperature (will shut off when below)
    "upper error threshold": [
        4011,
        "degC",
        122, # this should not exceed 125 and absolutely CANNOT exceed 150 
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
    "step": 0.1,  # allow 0.1 precision, not more
}

from app.param_values import PARAM_VALUES

# maximum absolute current
MAX_CURRENT = PARAM_VALUES["current limitation"][2]

# minimum difference between target and actual temperature to return MAX_CURRENT in °C
MIN_DELTA = 3.5

# no funny values
assert MIN_DELTA > 0

# TECs will heat until target+OFFSET_TEMP and cool above that
OFFSET_TEMP = .3


def compute_current(target_temp, avg_temp):
    """
    Returns the new current for TECs of the same plate based on the average temperature of the plate.
    """
    # when no target has been set
    if target_temp is None:
        return None

    # calculate how many MIN_DELTAs we are away from target
    heat_factor = (target_temp + OFFSET_TEMP - avg_temp) / MIN_DELTA

    # must be between 0 and 1
    if heat_factor > 1:
        heat_factor = 1

    # this should never happen
    if heat_factor < -1 or heat_factor > 1:
        raise ValueError("Something went wrong when computing new current for a plate.")

    # compute current
    # positive heat_factor -> target > avg -> heat -> negative current
    current = heat_factor * MAX_CURRENT * -1

    return float(current)

"""
These are the serialport allocations for the 4 boards controlling the TECs when connected via USB.
"""

# this many TECs in total
NUM_TECS = 8

PORTS = {
    "TOP_1": "COM5",
    "TOP_2": "COM6",
    "BOTTOM_1": "COM3",
    "BOTTOM_2": "COM4"
}

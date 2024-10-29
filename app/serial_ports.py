"""
These are the serialport allocations for the 4 boards controlling the TECs when connected via USB.
"""

# this many TECs in total
NUM_TECS = 8

# fill in serial ports here. See README for details.
PORTS = {
    "TOP_1": "Fill in port here",
    "TOP_2": "Fill in port here",
    "BOTTOM_1": "Fill in port here",
    "BOTTOM_2": "Fill in port here",
}

# make sure that all ports are filled in
if "Fill in port here" in PORTS.values():
    for i in range (3):
        print(
            f"[ERROR] Please fill in all serial ports. See README for details."
        )
    input("Press Enter to continue....")
    exit()

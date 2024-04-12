"""
Functions to send commands to the TECInterface
"""

import redis


UI_COMMANDS_CHANNEL = "ui_commands"

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def set_temperature(plate, temp):
    r.publish(UI_COMMANDS_CHANNEL, f"SET_TEMP$${plate}$${temp}")

def disable_all_plates():
    r.publish(UI_COMMANDS_CHANNEL, "DISABLE_ALL")
    
def enable_all_plates():
    r.publish(UI_COMMANDS_CHANNEL, "ENABLE_ALL")
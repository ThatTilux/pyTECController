"""
Functions to send commands to the TECInterface
"""

import redis

from redis_keys import REDIS_KEY_START_BACKEND_FEEDBACK, REDIS_KEY_UI_COMMANDS

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# subscribe pubsub channels
pubsub_backend_start_feedback = r.pubsub()
pubsub_backend_start_feedback.subscribe(REDIS_KEY_START_BACKEND_FEEDBACK)


def set_temperature(plate, temp):
    r.publish(REDIS_KEY_UI_COMMANDS, f"SET_TEMP$${plate}$${temp}")


def disable_all_plates():
    r.publish(REDIS_KEY_UI_COMMANDS, "DISABLE_ALL")


def enable_all_plates():
    r.publish(REDIS_KEY_UI_COMMANDS, "ENABLE_ALL")


def start_backend():
    """
    Start the backend and return True if successful, False otherwise.
    
    Returns
    -------
    bool
        True if the backend started successfully, False otherwise.
    """
    r.publish(REDIS_KEY_UI_COMMANDS, "GO")

    # wait for the backend to start
    return _wait_for_backend_response()
            
def start_backend_dummy():
    """
    Start the backend in dummy mode and return True if successful, False otherwise.
    
    Returns
    -------
    bool
        True if the backend started successfully, False otherwise.
    """
    r.publish(REDIS_KEY_UI_COMMANDS, "GO_DUMMY")

    # wait for the backend to start
    return _wait_for_backend_response()

def _wait_for_backend_response():
    """
    Wait for the backend to start and return True if successful, False otherwise.
    
    Returns
    -------
    bool
        True if the backend started successfully, False otherwise.
    """
    for message in pubsub_backend_start_feedback.listen():
        if message["type"] == "message":
            data = message["data"].split("$$") 
            if data[0] == "SUCCESS":
                return True
            elif data[0] == "ERROR":
                return False
            else:
                raise ValueError(f"Unknown message received: {message}")
"""
Connection parameters
"""

REDIS_HOST = "localhost"
REDIS_PORT = 6379

"""
Channel Keys
"""
# channel for the current data
REDIS_KEY_STORE = "tec-data-store"

# channel for the current data that is too old to be displayed
REDIS_KEY_STORE_ALL = "tec-data-store-all"

# recovered data from last session
REDIS_KEY_PREVIOUS_DATA = "tec-data-store-previous"

# channel for callback locks
REDIS_KEY_PREFIX_CALLBACK_LOCK = "tec-callback-lock:"

# inform UI of connection status of all TECs
REDIS_KEY_TEC_CONNECTION_STATUS = "tec-connection-status"

# inform the UI of success or error when starting backend
REDIS_KEY_START_BACKEND_FEEDBACK = "tec-start-backend-feedback"

# inform the UI that data acquisition is reconnecting
REDIS_KEY_RECONNECTING = "tec-data-reconnecting"

# pubsub channel for UI commands
REDIS_KEY_UI_COMMANDS = "ui_commands"
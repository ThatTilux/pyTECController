from ui.callbacks.buttons import button_callbacks
from ui.callbacks.graphs_tables import graphs_tables_callbacks
from ui.callbacks.misc import misc_callbacks
from ui.callbacks.sequence_rows import sequence_rows_callbacks


# all callbacks inside this function
def register_callbacks(app):

    button_callbacks(app)
    graphs_tables_callbacks(app)
    sequence_rows_callbacks(app)
    misc_callbacks(app)
    


from dash.dependencies import Output, Input
from dash import dcc
import pandas as pd
from tec_interface import TECInterface

_tec_interface: TECInterface = None

def tec_interface():
    global _tec_interface
    if _tec_interface is None:
        _tec_interface = TECInterface()
    return _tec_interface

# all callbacks inside this function
def register_callbacks(app):
    @app.callback(
        Output('tec-data-table', 'data'),
        Output('tec-data-table', 'columns'),
        Input('interval-component', 'n_intervals')
    )
    def update_table(n):
        # Fetch data from the TEC interface
        df = tec_interface()._get_data()

        # Preparing data for the DataTable
        columns = [{'name': i, 'id': i} for i in df.columns]
        data = df.to_dict('records')
        return data, columns

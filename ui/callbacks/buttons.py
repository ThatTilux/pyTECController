from datetime import datetime
from dash.dependencies import Output, Input, State
from dash import dcc
import dash

from ui.callbacks.graphs_tables import is_graph_paused, set_pause_sequence
from ui.command_sender import disable_all_plates, enable_all_plates, set_temperature
from ui.data_store import get_data_for_download, get_recovered_data


def button_callbacks(app):
    # when the download data btn is pressed
    @app.callback(
        Output("download-data-csv", "data"),
        [
            Input("btn-download-csv", "n_clicks"),
            State("checkboxes-download", "value"),
        ],
        prevent_initial_call=True,
    )
    def download_all_data(n_clicks, selected_options):
        df = get_data_for_download()

        # only keep selected columns and the timestamp
        selected_columns = selected_options + ["timestamp"]
        df = df[selected_columns]

        time = datetime.now()
        return dcc.send_data_frame(df.to_csv, f"TEC_data_{time}.csv")

    # when the recover data btn is pressed
    @app.callback(
        Output("download-data-csv", "data", allow_duplicate=True),
        Input("btn-download-recovered-csv", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_recovered_data(n_clicks):
        df = get_recovered_data()

        time = datetime.now()
        return dcc.send_data_frame(df.to_csv, f"TEC_data_{time}.csv")

    # when the pause graphs btn is pressed
    # the actual pausing happens in the callback that updates the graphs
    @app.callback(
        [Output("btn-pause-graphs", "children"), Output("btn-pause-graphs-2", "children")],
        [Input("btn-pause-graphs", "n_clicks"), Input("btn-pause-graphs-2", "n_clicks")],
        prevent_initial_call=True,
    )
    def handle_pause_graphs(n_clicks, n_clicks_2):
        btn_label = "Resume Graphs" if is_graph_paused(n_clicks, n_clicks_2) else "Freeze Graphs"

        return btn_label, btn_label
    
    
    # callback for when the pause sequence btn is pressed
    @app.callback(
        Output("btn-pause-sequence", "children"), 
        Input("btn-pause-sequence", "n_clicks")
    )
    def handle_pause_sequence(n_clicks):
        paused = n_clicks % 2 == 1
        
        # notify the sequence manager
        set_pause_sequence(paused)
        
        # return btn label
        if paused:
            return "Resume Sequence"
        return "Pause Sequence"
        

    # when the stop all tecs btn is pressed
    @app.callback(
        Output("btn-stop-all-tecs", "n_clicks"),  # dummy
        [Input("btn-stop-all-tecs", "n_clicks")],
        prevent_initial_call=True,
    )
    def stop_tecs(n_clicks):
        disable_all_plates()
        return dash.no_update

    # when the start btn is pressed
    @app.callback(
        [
            Output({"type": "set-target-temp-error", "index": "input-top-plate"}, "children"),
            Output({"type": "set-target-temp-error", "index": "input-bottom-plate"}, "children"),
        ],
        [
            Input("btn-start-tecs", "n_clicks"),
            State({"type": "set-target-temp", "index": "input-top-plate"}, "value"),
            State({"type": "set-target-temp", "index": "input-bottom-plate"}, "value"),
        ],
        prevent_initial_call=True,
    )
    def start_tecs(n_clicks, top_temp, bottom_temp):
        # the number input ensures that the temps are int or float or None

        # check if the fields were filled
        error_top = ""
        error_bottom = ""
        if top_temp is None:
            error_top = "Please enter a temperature."

        if bottom_temp is None:
            error_bottom = "Please enter a temperature."

        if not error_top and not error_bottom:
            top_temp = float(top_temp)
            bottom_temp = float(bottom_temp)

            # set temps and start all tecs
            set_temperature("top", top_temp)
            set_temperature("bottom", bottom_temp)

            enable_all_plates()

        return error_top, error_bottom

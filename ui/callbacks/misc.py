from dash.dependencies import Output, Input, State
import dash

from ui.data_store import detect_dummy


def misc_callbacks(app):
    # dummy mode detection
    @app.callback(
        Output("dummy-mode-container", "style"),
        Input("interval-dummy-detection", "n_intervals"),
    )
    def dummy_detection(n):
        if detect_dummy():
            # show the warning that dummy mode is on
            return {"display": "block"}
        return dash.no_update
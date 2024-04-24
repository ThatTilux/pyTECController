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

    # spinner for initial load
    @app.callback(
        [Output("app-main-content", "style"), Output("initial-load-spinner", "style")],
        Input("initial-load", "children"),
        prevent_initial_call=False,
    )
    def toggle_spinner(is_loaded):
        if is_loaded:
            return {"display": "block"}, {
                "display": "none"
            }  # Shot app content after initial load
        return {"display": "none"}, {"display": "block"}  # hide app content

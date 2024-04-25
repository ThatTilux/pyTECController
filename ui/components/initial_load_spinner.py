from dash import html
import dash_bootstrap_components as dbc


def initial_load_spinner():
    return html.Div(
        id="initial-load-spinner",
        children=dbc.Spinner(
            color="primary",
            fullscreen=True,
        ),
    )

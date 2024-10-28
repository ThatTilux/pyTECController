import dash_bootstrap_components as dbc
from dash import html

from ui.components.download_accordion import download_btn

def tec_error_page():
    """Page to overlay all content when a TEC has an error and is therefore disconnected.
    """
    return html.Div(
        style={
            'position': 'fixed',
            'top': 0,
            'left': 0,
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0, 0, 0, 0.7)',
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'zIndex': 9999
        },
        children=html.Div(
            style={
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.2)',
                'textAlign': 'center',
                'width': '500px'
            },
            children=[
                html.H2("Reconnecting", style={'marginBottom': '20px'}),
                dbc.Spinner(color="primary", spinner_class_name="mb-3"),
                html.P("Some TECs are have encountered an error and are currently rebooting. Trying to reconnect..."),
                download_btn("btn-download-csv-reconnecting", "Download data as CSV")
            ]
        )
    )

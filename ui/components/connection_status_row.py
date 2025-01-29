import dash_bootstrap_components as dbc
from dash import html

def connection_status_row(name, port, status=False):
    """
    Creates a row for displaying a device's connection status.

    :param name: The name of the device (e.g., "TOP_1")
    :param port: The port of the device (e.g., "COM5")
    :param status: Connection status (True for connected or False for not connected), defaults to False
    :return: dbc.Row component
    """
    status_color = "success" if status else "danger"
    status_text = "Connected" if status else "Not Connected"

    return dbc.Row(
        [
            dbc.Col(
                html.Span(f"{name} ({port})", className="fw-bold text-end"),
                width="auto",
            ),
            dbc.Col(
                dbc.Badge(status_text, color=status_color, className="px-3"),
                width="auto",
            ),
        ],
        className="align-items-center justify-content-between py-2",
    )

import dash_bootstrap_components as dbc
from dash import html


def connection_status_row(name, port, status=False, switch_value=True):
    """
    Creates a row for displaying a device's connection status.

    :param name: The name of the device (e.g., "TOP_1")
    :param port: The port of the device (e.g., "COM5")
    :param status: Connection status (True for connected or False for not connected), defaults to False
    :param switch_value: The value of the switch, defaults to True (ignored if the device is not optional)
    :return: dbc.Row component
    """
    status_color = "success" if status else "danger"
    status_text = "Connected" if status else "Not Connected"

    # Optional devices can be toggled on and off
    is_optional = "OPTIONAL" in name

    return dbc.Row(
        [
            dbc.Col(
                html.Div(
                    children=[
                        (
                            dbc.Switch(
                                id={"type": "toggle-tec-controller", "index": name},
                                label="",
                                value=switch_value,
                                className="align-self-center pt-1",
                                label_id=name,  # workaround to get TEC contrller name in callback
                            )
                            if is_optional
                            else None
                        ),
                        html.Span(name, className="fw-bold mb-0"),
                        html.Span(f" ({port})", className="mb-0"),
                    ],
                    className="d-flex align-items-center gap-2",
                ),
                width="auto",
            ),
            dbc.Col(
                dbc.Badge(status_text, color=status_color, className="px-3"),
                width="auto",
            ),
        ],
        className=f"align-items-center justify-content-between py-2 {'border-top mt-2' if is_optional else ''}",
    )

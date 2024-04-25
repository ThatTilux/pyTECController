from dash import html
import dash_bootstrap_components as dbc


def control_box(heading, children):
    """
    Box with centered heading and border.
    """
    return html.Div(
        [
            dbc.Row(
                dbc.Col(
                    html.H4(heading, style={"text-align": "center"}),
                    width={"size": 6, "offset": 3},
                ),
                className="mb-4",
            ),
            *children
        ],
        className="mb-3 p-4",
        style={"border": "1px solid #ddd", "borderRadius": "5px"},
    )

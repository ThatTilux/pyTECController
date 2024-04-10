from dash import html, dcc
import dash_bootstrap_components as dbc


def control_form():
    return html.Div(
        [
            dbc.Label("Set Target Temperatures"),
            dbc.Row(
                [
                    dbc.Label("Top Plate", width="auto"),
                    dbc.InputGroup(
                        [
                            dbc.Input(type="number", placeholder=""),
                            dbc.InputGroupText("°C"),
                        ]
                    ),
                    dbc.Label("Bottom Plate", width="auto"),
                    dbc.InputGroup(
                        [
                            dbc.Input(type="number", placeholder=""),
                            dbc.InputGroupText("°C"),
                        ]
                    ),
                ],
                class_name="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [dbc.Button(
                            "Freeze Graphs", id="btn-pause-graphs", color="secondary"
                        ),
                        dbc.Popover(
                            "This only pauses the graphs, not the TECs or data logging.",
                            target="btn-pause-graphs",
                            body=True,
                            trigger="hover",
                        )]
                    ),
                    html.Div(
                        [
                            dbc.Col(dbc.Button("Stop all TECs", color="danger")),
                            dbc.Col(dbc.Button("Write Config", color="primary")),
                        ]
                    ),
                ],
                justify="between",
            ),
        ],
        className="mb-5",
    )

from dash import html
import dash_bootstrap_components as dbc


def control_form_buttons():
    """
    Adds buttons to control the machine.
    """
    return html.Div(
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Freeze Graphs", id="btn-pause-graphs", color="secondary"
                    ),
                    width={"size": 4},
                ),
                dbc.Popover(
                    "This only pauses the graphs, not the TECs, data logging or the table below.",
                    target="btn-pause-graphs",
                    placement="bottom",
                    body=True,
                    trigger="hover",
                ),
                dbc.Col(
                    html.Div(
                        [
                            dbc.Button(
                                "Stop all TECs",
                                id="btn-stop-all-tecs",
                                color="danger",
                                style={"margin-right": "0.5em"},
                            ),
                            dbc.Button(
                                "Start",
                                id="btn-start-tecs",
                                color="primary",
                                class_name="ml-2",
                            ),
                        ]
                    ),
                    width="auto",
                    class_name="d-flex justify-content-end",
                ),
            ],
            justify="between",
            className="mt-3",
        )
    )


def control_sequence_buttons():
    """
    Adds buttons to control the sequences.
    """
    return html.Div(
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        children=[
                            dbc.Button(
                                "Freeze Graphs",
                                id="btn-pause-graphs-2",
                                color="secondary",
                                style={"margin-right": "0.5em"},
                            ),
                            dbc.Button(
                                "Pause Sequence",
                                disabled=True,
                                id="btn-pause-sequence",
                                color="secondary",
                                outline=True,
                                style={"margin-right": "0.5em"},
                            ),
                            dbc.Button(
                                "Skip Step",
                                disabled=True,
                                id="btn-skip-sequence-step",
                                color="secondary",
                                outline=True,
                            ),
                        ]
                    ),
                    width="auto"
                ),
                dbc.Popover(
                    "This only pauses the graphs, not the Sequence, data logging or the table below.",
                    target="btn-pause-graphs-2",
                    body=True,
                    placement="bottom",
                    trigger="hover",
                ),
                dbc.Popover(
                    "The sequence will not advance to the next step while it is paused.",
                    target="btn-pause-sequence",
                    body=True,
                    placement="bottom",
                    trigger="hover",
                ),
                dbc.Popover(
                    "Skip to the next step of the sequence.",
                    target="btn-skip-sequence-step",
                    body=True,
                    placement="bottom",
                    trigger="hover",
                ),
                dbc.Col(
                    html.Div(
                        [
                            dbc.Button(
                                "Abort",
                                id="btn-stop-sequence",
                                color="danger",
                                style={"margin-right": "0.5em"},
                            ),
                            dbc.Button(
                                "Start Sequence",
                                id="btn-submit-sequence",
                                color="primary",
                                class_name="ml-2",
                            ),
                        ]
                    ),
                    width="auto",
                    class_name="d-flex justify-content-end",
                ),
            ],
            justify="between",
            className="mt-3",
        )
    )

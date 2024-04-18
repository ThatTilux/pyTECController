from dash import html
import dash_bootstrap_components as dbc

from app.param_limits import TEMP_INPUT_LIMITS


def create_temperature_input(id, label):
    """
    Creates an input group for a temperature input field
    """

    popover_content = f"Expects temperatures between {TEMP_INPUT_LIMITS['min']} and {TEMP_INPUT_LIMITS['max']} with a maximum precision of {TEMP_INPUT_LIMITS['step']}."

    return html.Div(
        [
            dbc.InputGroup(
                [
                    dbc.InputGroupText(label),
                    dbc.Input(
                        type="number",
                        id=id,
                        min=TEMP_INPUT_LIMITS["min"],
                        max=TEMP_INPUT_LIMITS["max"],
                        step=TEMP_INPUT_LIMITS["step"],
                        style={"maxWidth": 100},
                    ),
                    dbc.InputGroupText("°C", id=id + "-group-text"),
                    dbc.Popover(
                        popover_content,
                        target=id + "-group-text",
                        body=True,
                        trigger="hover",
                    ),
                ],
            ),
            html.Div("", id=f"{id}-error", style={"color": "red"}),
        ],
        className="mb-3",
    )


def control_form():

    return html.Div(
        [
            dbc.Row(
                dbc.Col(
                    html.H4("Set Target Temperatures", style={"text-align": "center"}),
                    width={"size": 6, "offset": 3},
                ),
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            children=create_temperature_input(
                                "input-top-plate", "Top Plate"
                            )
                        ),
                        width=6,
                        class_name="d-flex justify-content-end",
                    ),
                    dbc.Col(
                        html.Div(
                            children=create_temperature_input(
                                "input-bottom-plate", "Bottom Plate"
                            )
                        ),
                        width=6,
                        class_name="d-flex justify-content-start",
                    ),
                ]
            ),
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
                                    style={"margin-right": "1em"},
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
            ),
        ],
        className="mb-3 p-4",
        style={"border": "1px solid #ddd", "borderRadius": "5px"},
    )

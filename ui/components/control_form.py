from dash import html
import dash_bootstrap_components as dbc

from app.param_values import TEMP_INPUT_LIMITS
from ui.components.control_box import control_box
from ui.components.control_buttons import control_form_buttons
from ui.components.input_group import input_group


def control_form():

    popover_content = "Enter target temperature."

    return control_box(
        heading="Set Target Temperature",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            children=input_group(
                                "set-target-temp",
                                "input-top-plate",
                                "Top Plate",
                                "°C",
                                popover_content,
                            )
                        ),
                        width=6,
                        class_name="d-flex justify-content-end",
                    ),
                    dbc.Col(
                        html.Div(
                            children=input_group(
                                "set-target-temp",
                                "input-bottom-plate",
                                "Bottom Plate",
                                "°C",
                                popover_content,
                            )
                        ),
                        width=6,
                        class_name="d-flex justify-content-start",
                    ),
                ]
            ),
            control_form_buttons(),
        ],
    )

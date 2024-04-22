from dash import html
import dash_bootstrap_components as dbc

from app.param_values import TEMP_INPUT_LIMITS
from ui.components.control_box import control_box
from ui.components.control_buttons import control_form_buttons, control_sequence_buttons
from ui.components.input_group import input_group


def btn_add_remove(row_index, btn_remove=True):
    """
    Adds a column for adding/removing a row
    """
    label = "-" if btn_remove else "+"
    action = "remove" if btn_remove else "add"
    return html.Div(
        dbc.Button(
            label,
            id={"type": "add-remove-btn", "index": row_index, "action": action},
            color="primary",
            style={"width": "40px", "fontWeight": "bold"},
        ),
    )


def sequence_btn_row(btn_id):
    """
    A row with a btn for adding a row.
    """
    return dbc.Row(
        [
            dbc.Col(
                btn_add_remove(btn_id, False),
                width=2,
                class_name="d-flex justify-content-center",
            )
        ],
        class_name="g-2",
    )


def sequence_input_row(id_prefix, row_id):
    """
    A row for the sequence input, i.e., one step of the sequence.
    """
    return dbc.Row(
        [
            dbc.Col(
                btn_add_remove(row_id, True),
                width=2,
                class_name="d-flex justify-content-center",
            ),
            dbc.Col(
                input_group(
                    f"{id_prefix}-top-plate",
                    f"{row_id}",
                    "Top Plate",
                    "°C",
                    "Target temperature for the top plate.",
                    min=TEMP_INPUT_LIMITS["min"],
                    max=TEMP_INPUT_LIMITS["max"],
                ),
                class_name="d-flex justify-content-end",
                width=2,
            ),
            dbc.Col(
                input_group(
                    f"{id_prefix}-bottom-plate",
                    f"{row_id}",
                    "Bot. Plate",
                    "°C",
                    "Target temperature for the bottom plate.",
                    min=TEMP_INPUT_LIMITS["min"],
                    max=TEMP_INPUT_LIMITS["max"],
                ),
                class_name="d-flex justify-content-center",
                width=2,
            ),
            dbc.Col(
                input_group(
                    f"{id_prefix}-num-steps",
                    f"{row_id}",
                    "Steps",
                    "n",
                    "The system will reach the target temperatures in this many steps.",
                    min=1,
                    max=100,
                ),
                class_name="d-flex justify-content-center",
                width=2,
            ),
            dbc.Col(
                input_group(
                    f"{id_prefix}-time-sleep",
                    f"{row_id}",
                    "Time",
                    "s",
                    "The system will wait for both plates to hold their target temperature for this long before advancing to the next step.",
                    min=0,
                    max=3_600,
                ),
                class_name="d-flex justify-content-start",
                width=2,
            ),
        ],
        class_name="g-2",
    )


def sequence_control_box():
    """
    A control box for creating and starting a sequence.
    """
    return control_box(
        heading="Start a Sequence",
        children=[
            html.Div(id="dynamic-sequence-rows"),  # rows are inserted via callback
            sequence_btn_row("sequence-btn-add-row"),
            control_sequence_buttons(),
        ],
    )

from dash import html
import dash_bootstrap_components as dbc

from app.param_values import TEMP_INPUT_LIMITS


def input_group(input_type, input_id, label, unit, popover_content, min=0, max=TEMP_INPUT_LIMITS["max"], step=TEMP_INPUT_LIMITS["step"], value=None):
    """
    Creates an input group with a popover.
    """
    
    popover_content = popover_content+f"\nExpects values between {min} and {max}."

    return html.Div(
        [
            dbc.InputGroup(
                [
                    dbc.InputGroupText(label),
                    dbc.Input(
                        type="number",
                        id={"type": input_type, "index": input_id},
                        min=min,
                        max=max,
                        step=step,
                        value=value,
                        style={"maxWidth": 100},
                    ),
                    dbc.InputGroupText(unit, id=f"{input_type}-group-text-{input_id}"),
                    dbc.Popover(
                    popover_content,
                        target=f"{input_type}-group-text-{input_id}",
                        body=True,
                        trigger="hover",
                        placement="bottom",
                    ),
                ],
            ),
            html.Div("", id={"type": f"{input_type}-error", "index": input_id}, style={"color": "red"}),
        ],
        className="mb-3",
    )

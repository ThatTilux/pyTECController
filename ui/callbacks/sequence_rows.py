import dash
from dash.dependencies import Output, Input, State, ALL
from dash import ctx
import json

from ui.command_sender import disable_all_plates
from ui.components.sequence_control_box import sequence_input_row


def sequence_rows_callbacks(app):
    # fills the div with sequence rows based on the Store
    @app.callback(
        Output("dynamic-sequence-rows", "children"),
        Input("visible-sequence-rows", "data"),
        prevent_initial_callback=False,
    )
    def render_rows(rows_indices):
        return [sequence_input_row("sequence-row", row_id=i) for i in rows_indices]

    # updates the store with the row indices based on pressed buttons
    @app.callback(
        Output("visible-sequence-rows", "data"),
        Input({"type": "add-remove-btn", "index": ALL, "action": ALL}, "n_clicks"),
        State("visible-sequence-rows", "data"),
        prevent_initial_call=True,
    )
    def update_rows(n_clicks, rows):
        # get which btn was pressed
        changed_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if changed_id:
            # get the action info
            action_info = json.loads(changed_id)
            # get index of affected row
            row_index = action_info["index"]
            # get the action (add/remove)
            if action_info["action"] == "add":
                rows.append(max(rows) + 1)  # Append new row index
            elif action_info["action"] == "remove":
                if len(rows) > 1:  # Ensure at least one row remains
                    rows.remove(row_index)
        return rows

    # processes the form input fields on btn press
    @app.callback(
        [
            Output({"type": "sequence-row-top-plate-error", "index": ALL}, "children"),
            Output(
                {"type": "sequence-row-bottom-plate-error", "index": ALL}, "children"
            ),
            Output({"type": "sequence-row-num-steps-error", "index": ALL}, "children"),
            Output({"type": "sequence-row-time-sleep-error", "index": ALL}, "children"),
            Output({"type": "sequence-row-top-plate", "index": ALL}, "disabled"),
            Output({"type": "sequence-row-bottom-plate", "index": ALL}, "disabled"),
            Output({"type": "sequence-row-num-steps", "index": ALL}, "disabled"),
            Output({"type": "sequence-row-time-sleep", "index": ALL}, "disabled"),
            Output("btn-submit-sequence", "disabled")
        ],
        [
            Input("btn-submit-sequence", "n_clicks"),
            Input("btn-stop-sequence", "n_clicks"),
        ],
        [
            State({"type": "sequence-row-top-plate", "index": ALL}, "value"),
            State({"type": "sequence-row-bottom-plate", "index": ALL}, "value"),
            State({"type": "sequence-row-num-steps", "index": ALL}, "value"),
            State({"type": "sequence-row-time-sleep", "index": ALL}, "value"),
        ],
        prevent_initial_call=True,
    )
    def process_sequence_values(
        n_clicks_submit,
        n_clicks_stop,
        top_plate_values,
        bottom_plate_values,
        num_steps_values,
        time_sleep_values,
    ):
        # get the button that triggered this callback
        if not ctx.triggered:
            return dash.no_update
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Initialize an empty list for each error message
        error_messages = [
            [""] * len(values)
            for values in [
                top_plate_values,
                bottom_plate_values,
                num_steps_values,
                time_sleep_values,
            ]
        ]
        # disabled states of all input fields
        disable_states = [
            [False] * len(values)
            for values in [
                top_plate_values,
                bottom_plate_values,
                num_steps_values,
                time_sleep_values,
            ]
        ]
        
        btn_submit_disabled = False

        # if the callback was initiated through the stop button, enable the input fields
        # TODO actually stop the sequence
        if "btn-stop-sequence" in button_id:
            # stop the TECs
            disable_all_plates()
            # enable all input fields and clear errors
            return *error_messages, *disable_states, btn_submit_disabled

        # this will be returned
        results = []
        
        found_error = False

        for i, (top_temp, bottom_temp, num_steps, time_sleep) in enumerate(
            zip(
                top_plate_values,
                bottom_plate_values,
                num_steps_values,
                time_sleep_values,
            )
        ):
            if None in [top_temp, bottom_temp, num_steps, time_sleep]:
                found_error=True
                if top_temp is None:
                    error_messages[0][i] = "Please enter a temperature."
                if bottom_temp is None:
                    error_messages[1][i] = "Please enter a temperature."
                if num_steps is None:
                    error_messages[2][i] = "Please enter a number."
                if time_sleep is None:
                    error_messages[3][i] = "Please enter a number."
                break  # only raise errors for one 
            else:
                # Parse input
                results.append((top_temp, bottom_temp, num_steps, time_sleep))

        if not found_error:
            # Disable all inputs if no error
            disable_states = [
                [True] * len(values) for values in disable_states
            ]  
            btn_submit_disabled=True

        return *error_messages, *disable_states, btn_submit_disabled

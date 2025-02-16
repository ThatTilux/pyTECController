import dash
from dash.dependencies import Output, Input, State, ALL
from dash import ctx
import json

from ui.callbacks.graphs_tables import set_sequence, stop_sequence
from ui.command_sender import disable_all_plates
from ui.components.sequence_control_box import sequence_input_row


def sequence_rows_callbacks(app):
    # fills the div with sequence rows based on the Store
    @app.callback(
        Output("dynamic-sequence-rows", "children"),
        Input("visible-sequence-rows", "data"),
        [
            State({"type": "sequence-row-top-plate-error", "index": ALL}, "children"),
            State(
                {"type": "sequence-row-bottom-plate-error", "index": ALL}, "children"
            ),
            State({"type": "sequence-row-num-steps-error", "index": ALL}, "children"),
            State({"type": "sequence-row-time-sleep-error", "index": ALL}, "children"),
        ],
        prevent_initial_callback=False,
    )
    def render_rows(
        rows_data,
        top_plate_errors,
        bottom_plate_errors,
        num_steps_errors,
        time_sleep_errors,
    ):
        row_keys = list(map(int, rows_data.keys()))  # Convert keys to integers

        error_msg = list(zip(
            top_plate_errors, bottom_plate_errors, num_steps_errors, time_sleep_errors
        ))

        return [
            sequence_input_row(
            "sequence-row",
            row_id=row_key,
            data=rows_data[str(row_key)],
            error_msg=error_msg[index] if index < len(error_msg) else None,
            )
            for index, row_key in enumerate(row_keys)
        ]

    # updates the store with the row indices based on pressed buttons
    # this callback triggeres a re-render of the rows, therefore the values in the input fields are saved here as well
    @app.callback(
        Output("visible-sequence-rows", "data"),
        [
            Input("btn-submit-sequence", "n_clicks"),
            Input({"type": "add-remove-btn", "index": ALL, "action": ALL}, "n_clicks"),
        ],
        [
            State({"type": "sequence-row-top-plate", "index": ALL}, "value"),
            State({"type": "sequence-row-bottom-plate", "index": ALL}, "value"),
            State({"type": "sequence-row-num-steps", "index": ALL}, "value"),
            State({"type": "sequence-row-time-sleep", "index": ALL}, "value"),
            State("visible-sequence-rows", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_rows(
        n_clicks_submit,
        n_clicks,
        top_data,
        bottom_data,
        num_steps_data,
        time_sleep_data,
        rows_data,
    ):
        # save all the data
        # *_data should all have the same length
        # first index of the top_data ... corresponds to the lowest rows_data index
        row_keys = list(map(int, rows_data.keys()))  # Convert keys to integers
        row_keys.sort()  # make sure they are sorted

        # get all the values
        for data_index, row_index in enumerate(row_keys):
            if data_index < len(top_data):
                rows_data[str(row_index)] = [
                    top_data[data_index],
                    bottom_data[data_index],
                    num_steps_data[data_index],
                    time_sleep_data[data_index],
                ]
            else:
                # if the inout fields are not rendered yet, no data
                rows_data[str(row_index)] = []

        # Check if there is at least one button click
        # dash triggeres this callback on startup for some reason; this checks that
        if not any(click is not None for click in n_clicks):
            return rows_data  # No button has been clicked; return the existing data unchanged

        # if the user spams a btn, this callback might be executed twice with same input
        # this leads to an IndexError/KeyError.
        try:
            # Check if the submit btn triggered this callback
            triggered_id = ctx.triggered_id
            if triggered_id == "btn-submit-sequence":
                # The submit button was clicked; just update the data
                return rows_data

            # callback was triggered by add/remove btn. Determine which one
            changed_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if changed_id:
                # get the action info
                action_info = json.loads(changed_id)
                # get index of affected row
                row_index = action_info["index"]

                # get the action (add/remove)
                if action_info["action"] == "add":
                    rows_data[str(max(row_keys) + 1)] = [
                        None,
                        None,
                        None,
                        None,
                    ]  # Append new row index
                elif action_info["action"] == "remove":
                    if len(rows_data) > 1:  # Ensure at least one row remains
                        rows_data.pop(str(row_index))
        except (IndexError, KeyError) as e:
            return dash.no_update
        return rows_data

    # processes the form input fields on btn press
    @app.callback(
        [
            Output({"type": "sequence-row-top-plate-error", "index": ALL}, "children"),
            Output(
                {"type": "sequence-row-bottom-plate-error", "index": ALL}, "children"
            ),
            Output({"type": "sequence-row-num-steps-error", "index": ALL}, "children"),
            Output({"type": "sequence-row-time-sleep-error", "index": ALL}, "children"),
            Output("is-sequence-running", "data"),
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
        # get the id that triggered this callback
        if not ctx.triggered:
            return dash.no_update

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

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

        valid_sequence = False

        # if the callback was initiated through the stop button or the stop trigger, enable the input fields and stop TECs
        if "btn-stop-sequence" in triggered_id:
            # stop the TECs
            disable_all_plates()
            # tell the sequence manager
            stop_sequence()
            # enable all input fields and clear errors
            return *error_messages, False

        # this will be used to create a sequence
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
            # special case for the first num_steps
            if i == 0 and num_steps != 1:
                found_error = True
                error_messages[2][i] = "The first step has to be 1."

            if None in [top_temp, bottom_temp, num_steps, time_sleep]:
                found_error = True
                if top_temp is None:
                    error_messages[0][i] = "Input invalid."
                if bottom_temp is None:
                    error_messages[1][i] = "Input invalid."
                if num_steps is None:
                    error_messages[2][i] = "Input invalid."
                if time_sleep is None:
                    error_messages[3][i] = "Input invalid."
                break  # only raise errors for one row
            else:
                # Parse input
                results.append((top_temp, bottom_temp, num_steps, time_sleep))

        if not found_error:
            # Disable all inputs if no error
            valid_sequence = True

            # create the sequence
            if len(results) > 0:
                set_sequence(results)

        return *error_messages, valid_sequence

    # update disabled states of sequence UI
    @app.callback(
        [
            Output({"type": "sequence-row-top-plate", "index": ALL}, "disabled"),
            Output({"type": "sequence-row-bottom-plate", "index": ALL}, "disabled"),
            Output({"type": "sequence-row-num-steps", "index": ALL}, "disabled"),
            Output({"type": "sequence-row-time-sleep", "index": ALL}, "disabled"),
            Output({"type": "add-remove-btn", "index": ALL, "action": ALL}, "disabled"),
            Output("btn-submit-sequence", "disabled"),
            Output("btn-pause-sequence", "disabled"),
            Output("btn-skip-sequence-step", "disabled"),
        ],
        [
            Input("is-sequence-running", "data"),
        ],
        [
            State(
                {"type": "sequence-row-top-plate", "index": ALL}, "value"
            ),  # needed to get number of rows
        ],
    )
    def sequence_status_change(is_sequence_running, top_plate_values):
        disable_submit_sequence = is_sequence_running
        disable_pause_sequence = not is_sequence_running
        disable_skip_sequence_step = not is_sequence_running

        form_fields_disabled = [
            [is_sequence_running] * len(values)
            for values in [
                top_plate_values,
                top_plate_values,
                top_plate_values,
                top_plate_values,
            ]
        ]

        add_remove_btns_disabled = [[is_sequence_running] * (len(top_plate_values) + 1)]

        return (
            *form_fields_disabled,
            *add_remove_btns_disabled,
            disable_submit_sequence,
            disable_pause_sequence,
            disable_skip_sequence_step,
        )

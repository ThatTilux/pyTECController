from dash import html
import dash_bootstrap_components as dbc


def welcome_menu():
    """
    The welcome menu to check TEC connections and start the backend.
    """
    return html.Div(
        children=[
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Connect TEC Controllers"), close_button=False),
                    dbc.ModalBody(
                        dbc.Spinner(
                            html.Div(id="connection-status-container"),
                            color="primary",
                        ), class_name="py-1"
                    ),
                    dbc.ModalFooter(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "Dummy Mode",
                                        id="btn-start-backend-dummy",
                                        color="danger",
                                        outline=True,
                                    ),
                                    width="auto",
                                ),
                                dbc.Popover(
                                    "Show pre-recorded data instead of connecting to the TECs.",
                                    target="btn-start-backend-dummy",
                                    placement="bottom",
                                    body=True,
                                    trigger="hover",
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Refresh",
                                                id="btn-refresh-tec-connection-status",
                                                color="success",
                                                style={"margin-right": "0.5em"},
                                            ),
                                            dbc.Spinner(
                                                html.Div(
                                                    dbc.Button(
                                                        "Start",
                                                        id="btn-start-backend",
                                                        color="primary",
                                                        disabled=True,
                                                    ),
                                                    id="spinner-btn-start-backend",
                                                ),
                                                color="primary",
                                                type="grow",
                                            ),
                                        ],
                                        className="d-flex justify-content-end",
                                    ),
                                    width="auto",
                                ),
                            ],
                            justify="between",
                            class_name="w-100",
                        )
                    ),
                ],
                backdrop=False,
                size="lg",
                is_open=True,
                centered=True,
                id="modal-connect-tecs",
            ),
            dbc.Toast(  # Toast for error on pressing the start btn
                [
                    html.P(
                        "Could not connect to the TECs. Please make sure they are powered on and connected via USB.",
                        className="mb-0",
                    )
                ],
                id="toast-start-backend-error",
                header="Error",
                icon="danger",
                duration=15000,
                is_open=False,
                # position toast on top right
                style={"position": "fixed", "top": 10, "right": 10, "width": 350},
            ),
        ]
    )

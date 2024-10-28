import dash_bootstrap_components as dbc
from dash import html


def download_accordion():
    return dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    html.P("Select applicable columns:"),
                    dbc.Checklist(
                        id="checkboxes-download",
                        options=[
                            {"label": "Loop Status", "value": "loop status"},
                            {
                                "label": "Object Temperature",
                                "value": "object temperature",
                            },
                            {
                                "label": "Target Temperature",
                                "value": "target object temperature",
                            },
                            {"label": "Output Current", "value": "output current"},
                            {"label": "Output Voltage", "value": "output voltage"},
                            {"label": "Output Power", "value": "output power"},
                        ],
                        value=[
                            "loop status",
                            "object temperature",
                            "target object temperature",
                            "output current",
                            "output voltage",
                            "output power",
                        ],  # Default selected
                    ),
                    download_btn('btn-download-csv'),
                ],
                title="Download Data",
            ),
            dbc.AccordionItem(
                children=[
                    html.P(
                        "You might be able to recover the data from your previous session here:"
                    ),
                    dbc.Button(
                        "Download recovered data as CSV",
                        color="primary",
                        id="btn-download-recovered-csv",
                        class_name="mt-2",
                    ),
                ],
                title="Recover Data",
            ),
        ],
        start_collapsed=True,
        class_name="mt-3 mb-3",
    )


def download_btn(id, label="Download as CSV"):
    return dbc.Button(
        label,
        color="primary",
        id=id,
        class_name="mt-2",
    )

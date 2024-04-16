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
                            {
                                "label": "Loop Status",
                                "value": "loop status"},
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
                        ],
                        value=[
                            "loop status",
                            "object temperature",
                            "target object temperature",
                            "output current",
                            "output voltage",
                        ],  # Default selected
                    ),
                    dbc.Button("Download as CSV ", color="primary", id="btn-download-csv", class_name="mt-2"),
                ],
                title="Download data",
            )
        ],
        start_collapsed=True,
        class_name="mt-3 mb-3"
    )

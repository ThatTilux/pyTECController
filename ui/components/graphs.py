import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


# remove these buttons from all graphs
GRAPH_BUTTONS_TO_REMOVE = ["lasso2d", "select2d", "autoScale2d"]


def graphs():
    return html.Div(
        [
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        [
                            graph_with_config("graph-object-temperature"),
                            html.Div(
                                [
                                    dbc.Label("Y-Axis Range:"),
                                    dbc.Checklist(
                                        options=[{"label": "Autoscale", "value": True}],
                                        id="avg-temperature-autoscale",
                                        class_name="ml-2",
                                        switch=True,
                                        value=[True],
                                    ),
                                    dbc.Col(
                                        dbc.InputGroup(
                                            [
                                                dbc.Input(
                                                    placeholder="min",
                                                    type="number",
                                                    id="avg-temperature-yaxis-min",
                                                ),
                                                dbc.Input(
                                                    placeholder="max",
                                                    type="number",
                                                    id="avg-temperature-yaxis-max",
                                                ),
                                            ],
                                        ),
                                        width=4,
                                    ),
                                ],
                                className="ms-5",
                            ),
                        ]
                    )
                ),
                class_name="mt-3 mb-3",
            ),
            graph_tabs(
                [
                    ("Temperature", graph_with_config("graph-all-temperature"), None),
                    ("Current", graph_with_config("graph-all-current"), None),
                    ("Voltage", graph_with_config("graph-all-voltage"), None),
                ]
            ),
        ]
    )


def graph_with_config(id):
    """
    Creates a graph with a predefined configuration
    """
    return dcc.Graph(
        id=id,
        config={"modeBarButtonsToRemove": GRAPH_BUTTONS_TO_REMOVE},
    )


def graph_tabs(graphs):
    """
    Tabs for graphs. Each tab has 2 graphs side by side (only 1 on md and smaller or if only 1 graph is provided)
    Format: [(label, graph1, graph2 | None)]
    """

    def card_content(graph1, graph2):
        if graph2 is None:
            return dbc.Col(html.Div(graph1), width=12)
        else:
            return [
                dbc.Col(
                    html.Div(graph1),
                    width=12,
                    md=6,
                ),
                dbc.Col(
                    html.Div(graph2),
                    width=12,
                    md=6,
                ),
            ]

    return dbc.Tabs(
        id="graph-tabs",
        children=[
            dbc.Tab(
                dbc.Card(
                    dbc.CardBody(dbc.Row(card_content(graph1, graph2))),
                    class_name="mt-3",
                ),
                tab_id=f"tab-{label.lower()}",
                label=label,
            )
            for label, graph1, graph2 in graphs
        ],
    )


def format_timestamps(df):
    """
    Formats timestamps tp the hh:mm:ss format
    """
    df["timestamp"] = df["timestamp"].dt.strftime("%H:%M:%S")


def _force_two_ticks(fig, df):
    """
    Force the fig to have 2 ticks only, namely the first and last timestamp
    """
    if df.empty:
        return

    first_timestamp = df["timestamp"].iloc[0]
    last_timestamp = df["timestamp"].iloc[-1]

    fig.update_xaxes(
        tickmode="array",
        tickvals=[first_timestamp, last_timestamp],
        ticktext=[first_timestamp, last_timestamp],
    )


def update_graph_object_temperature(df, yaxis_range):

    # Group by Plate and Timestamp, then calculate mean
    avg_temps = (
        df.groupby(["Plate", "timestamp"])["object temperature"].mean().reset_index()
    )

    # reset multiindex
    temp_df = df.reset_index()

    # Extract the first target temperature for each Plate at each timestamp
    target_temps = temp_df.drop_duplicates(subset=["Plate", "timestamp"])[
        ["Plate", "timestamp", "target object temperature"]
    ]

    # Format the Timestamps to hh:mm:ss
    format_timestamps(avg_temps)
    format_timestamps(target_temps)

    # color map for all lines
    color_map = {"top": "red", "bottom": "blue"}

    # labels in the legend
    label_map = {"top": "Top", "bottom": "Bottom"}

    fig = px.line(
        avg_temps,
        x="timestamp",
        y="object temperature",
        color="Plate",
        labels={
            "timestamp": "Time (hh:mm:ss)",
            "object temperature": "Temperature (°C)",
            "Plate": "",  # Remove the default legend title
        },
        title="Average Plate Temperatures",
        markers=True,
        color_discrete_map=color_map,
    )

    # add custom legend title
    fig.for_each_trace(lambda trace: trace.update(name=label_map[trace.name]))

    # custom yaxis range
    if yaxis_range:
        fig.update_layout(yaxis={"range": yaxis_range})

    # Add lines for target object temperatures
    for plate in target_temps["Plate"].unique():
        plate_target_temps = target_temps[target_temps["Plate"] == plate]
        fig.add_trace(
            go.Scatter(
                x=plate_target_temps["timestamp"],
                y=plate_target_temps["target object temperature"],
                mode="lines",
                name=f"Target Temperature ({plate})",
                line=dict(color=color_map[plate], width=2, dash="dash"),
                showlegend=False,
            )
        )

    # dummy trace for target temperature indication in the legend
    fig.add_trace(
        go.Scatter(
            x=[None],  # No actual data
            y=[None],
            mode="lines",
            name="Target",
            line=dict(color="gray", width=2, dash="dash"),
            showlegend=True,
        )
    )

    # force the plot to always only have 2 ticks
    _force_two_ticks(fig, avg_temps)

    return fig


def update_graph_max_abs_generic(df, parameter, label, unit):
    """
    Generic function for updating a graph displaying the absolute max of some value.

    parameter: name of the parameter, e.g. "output current"
    label: label to display, e.g. "Current"
    unit: label of unit, e.g. "A"
    """

    # Keep only necessary columns
    df = df[[parameter, "timestamp"]]

    # Group by timestamp first
    grouped_by_timestamp = df.groupby("timestamp")

    # Find the value with the maximum absolute value in each group
    max_abs = (
        grouped_by_timestamp[parameter]
        .apply(lambda x: x.loc[x.abs().idxmax()])
        .reset_index()
    )

    # format timestamps
    format_timestamps(max_abs)

    fig = px.line(
        max_abs,
        x="timestamp",
        y=parameter,
        labels={
            "timestamp": "Time (hh:mm:ss)",
            parameter: f"{label} ({unit})",
        },
        title=f"Maximum Absolute {label} drawn by any TEC",
        markers=True,
    )

    # force the plot to always only have 2 ticks
    _force_two_ticks(fig, max_abs)

    return fig


def update_graph_max_voltage(df):
    return update_graph_max_abs_generic(df, "output voltage", "Voltage", "V")


def update_graph_max_current(df):
    return update_graph_max_abs_generic(df, "output current", "Current", "A")


def update_graph_all_generic(_df, parameter, label, unit):
    """
    Generic function for updating a graph displaying all instances of some parameter.

    parameter: name of the parameter, e.g. "output current"
    label: label to display, e.g. "Current"
    unit: label of unit, e.g. "A"
    """

    # reset multiindex
    df = _df.reset_index()

    # Create a 'Label' column
    df["Label"] = df["Plate"].str.upper() + "_" + df["TEC"].astype(str)

    # Keep only necessary columns
    df = df[["Label", parameter, "timestamp"]]

    # Blue for all bottom ones and red for all top
    colors = {
        f"BOTTOM_{i}": f"rgba(0, 0, {255 - 40*i}, 1.0)"
        for i in range(df["Label"].nunique())
    }
    colors.update(
        {
            f"TOP_{i}": f"rgba({255 - 30*i}, 0, 0, 1.0)"
            for i in range(df["Label"].nunique())
        }
    )

    # format timestamps
    format_timestamps(df)

    fig = px.line(
        df,
        x="timestamp",
        y=parameter,
        color="Label",
        color_discrete_map=colors,
        labels={
            "timestamp": "Time (hh:mm:ss)",
            parameter: f"{label} ({unit})",
        },
        title=f"{label} for all TECs",
        markers=True,
    )

    # force the plot to always only have 2 ticks
    _force_two_ticks(fig, df)

    return fig


def update_graph_all_current(df):
    return update_graph_all_generic(df, "output current", "Current", "A")


def update_graph_all_voltage(df):
    return update_graph_all_generic(df, "output voltage", "Voltage", "V")


def update_graph_all_temperature(df):
    return update_graph_all_generic(df, "object temperature", "Temperature", "°C")

import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


# remove these buttons from all graphs
GRAPH_BUTTONS_TO_REMOVE = ["lasso2d", "select2d", "autoScale2d"]

# dictionary for yaxis ranges
# format: id: [ymin, ymax]
graph_yaxis_ranges = {}


def graphs(app):
    return html.Div(
        [
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        children=graph_with_config_and_controls(
                            app, "graph-object-temperature"
                        )
                    )
                ),
                class_name="mt-3 mb-3",
            ),
            graph_tabs(
                id="graph-tabs",
                active_tab="tab-temperature",
                graphs_with_controls=[
                    (
                        "Temperature",
                        graph_with_config_and_controls(app, "graph-all-temperature"),
                        None,
                    ),
                    (
                        "Current",
                        graph_with_config_and_controls(app, "graph-all-current"),
                        None,
                    ),
                    (
                        "Voltage",
                        graph_with_config_and_controls(app, "graph-all-voltage"),
                        None,
                    ),
                    (
                        "Power",
                        graph_with_config_and_controls(app, "graph-sum-power"),
                        None,
                    ),
                ],
            ),
            html.Div(
                graph_tabs(
                    id="graph-tabs-2",
                    active_tab="tab-current",
                    graphs_with_controls=[
                        (
                            "Temperature",
                            graph_with_config_and_controls(
                                app, "graph-all-temperature-2"
                            ),
                            None,
                        ),
                        (
                            "Current",
                            graph_with_config_and_controls(app, "graph-all-current-2"),
                            None,
                        ),
                        (
                            "Voltage",
                            graph_with_config_and_controls(app, "graph-all-voltage-2"),
                            None,
                        ),
                        (
                            "Power",
                            graph_with_config_and_controls(app, "graph-sum-power-2"),
                            None,
                        ),
                    ],
                ),
                className="mt-3",
            ),
        ]
    )


def graph_with_config_and_controls(app, id):
    """
    Creates a graph with a predefined configuration
    """
    graph = dcc.Graph(
        id=id,
        config={"modeBarButtonsToRemove": GRAPH_BUTTONS_TO_REMOVE},
    )

    controls = html.Div(
        children=[
            dbc.Button(
                "Show Y-Axis Controls",
                id=f"{id}-yaxis-btn-toggle",
                class_name="ms-5 mb-1",
            ),
            html.Div(
                id=f"{id}-yaxis-controls-container",
                style={"display": "none"},
                children=[
                    dbc.Label("Y-Axis Range:"),
                    dbc.Checklist(
                        options=[{"label": "Autoscale", "value": True}],
                        id=f"{id}-yaxis-autoscale",
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
                                    id=f"{id}-yaxis-min",
                                    disabled=True,
                                ),
                                dbc.Input(
                                    placeholder="max",
                                    type="number",
                                    id=f"{id}-yaxis-max",
                                    disabled=True,
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

    # register yaxis callbacks
    @app.callback(
        [
            Output(f"{id}-yaxis-controls-container", "style"),
            Output(f"{id}-yaxis-btn-toggle", "children"),
        ],
        Input(f"{id}-yaxis-btn-toggle", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_yaxis_container(n_clicks):
        display = "none"
        btn_label = "Show Y-Axis Controls"
        if n_clicks is not None and n_clicks % 2 == 1:
            display = "block"
            btn_label = "Hide Y-Axis Controls"
        return {"display": display}, btn_label

    @app.callback(
        [
            Output(f"{id}-yaxis-min", "disabled"),
            Output(f"{id}-yaxis-max", "disabled"),
        ],
        [
            Input(f"{id}-yaxis-autoscale", "value"),
            Input(f"{id}-yaxis-min", "value"),
            Input(f"{id}-yaxis-max", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_yaxis(autoscale, ymin, ymax):
        disabled = False
        if autoscale:
            yaxis_range = None
            disabled = True
        else:
            yaxis_range = [ymin, ymax]

        # update dict
        global graph_yaxis_ranges
        graph_yaxis_ranges[id] = yaxis_range

        return disabled, disabled

    # return
    return [graph, controls]


def graph_tabs(id, graphs_with_controls, active_tab=""):
    """
    Tabs for graphs. Each tab has 2 graphs side by side (only 1 on md and smaller or if only 1 graph is provided)
    Format: [(label, [graph1, controls1], [graph2, controls2] or None)]
    """

    def card_content(graph1_with_controls, graph2_with_controls):
        graph1, controls1 = graph1_with_controls

        if graph2_with_controls is None:
            return dbc.Col(html.Div(children=[graph1, controls1]), width=12)
        else:
            graph2, controls2 = graph2_with_controls
            return [
                dbc.Col(
                    html.Div(children=[graph1, controls1]),
                    width=12,
                    md=6,
                ),
                dbc.Col(
                    html.Div(children=[graph2, controls2]),
                    width=12,
                    md=6,
                ),
            ]

    return dbc.Tabs(
        id=id,
        children=[
            dbc.Tab(
                dbc.Card(
                    dbc.CardBody(
                        dbc.Row(
                            children=card_content(
                                graph1_with_controls, graph2_with_controls
                            )
                        )
                    ),
                    class_name="mt-3",
                ),
                tab_id=f"tab-{label.lower()}",
                label=label,
            )
            for label, graph1_with_controls, graph2_with_controls in graphs_with_controls
        ],
        active_tab=active_tab,
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


def set_yaxis(fig_id, fig):
    # custom yaxis range
    global graph_yaxis_ranges
    try:
        yaxis_range = graph_yaxis_ranges[fig_id]
        if yaxis_range:
            fig.update_layout(yaxis={"range": yaxis_range})
    except KeyError:  # no yaxis was set
        pass


def update_graph_object_temperature(df, fig_id):

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

    # set yaxis
    set_yaxis(fig_id=fig_id, fig=fig)

    # add custom legend title
    fig.for_each_trace(lambda trace: trace.update(name=label_map[trace.name]))

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


def update_graph_max_abs_generic(df, parameter, label, unit, fig_id):
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

    # set yaxis
    set_yaxis(fig_id=fig_id, fig=fig)

    # force the plot to always only have 2 ticks
    _force_two_ticks(fig, max_abs)

    return fig


def update_graph_max_voltage(df, fig_id):
    return update_graph_max_abs_generic(df, "output voltage", "Voltage", "V", fig_id)


def update_graph_max_current(df, fig_id):
    return update_graph_max_abs_generic(df, "output current", "Current", "A", fig_id)


def update_graph_all_generic(_df, parameter, label, unit, fig_id):
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
        "TOP_0": "rgba(255, 0, 0, 1.0)",
        "TOP_1": "rgba(255, 0, 140, 1.0)",
        "TOP_2": "rgba(255, 0, 238, 1.0)",
        "TOP_3": "rgba(183, 0, 255, 1.0)",
        "BOTTOM_0": "rgba(0, 0, 255, 1.0)",
        "BOTTOM_1": "rgba(0, 136, 255, 1.0)",
        "BOTTOM_2": "rgba(0, 208, 255, 1.0)",
        "BOTTOM_3": "rgba(0, 255, 234, 1.0)",
    }

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

    # set yaxis
    set_yaxis(fig_id=fig_id, fig=fig)

    # force the plot to always only have 2 ticks
    _force_two_ticks(fig, df)

    return fig


def update_graph_all_current(df, fig_id):
    return update_graph_all_generic(df, "output current", "Current", "A", fig_id)


def update_graph_all_voltage(df, fig_id):
    return update_graph_all_generic(df, "output voltage", "Voltage", "V", fig_id)


def update_graph_all_temperature(df, fig_id):
    return update_graph_all_generic(
        df, "object temperature", "Temperature", "°C", fig_id
    )


def update_graph_sum_generic(_df, parameter, label, unit, fig_id):
    """
    Generic function for updating a graph displaying the sum of some parameter.

    parameter: name of the parameter, e.g. "output current"
    label: label to display, e.g. "Current"
    unit: label of unit, e.g. "A"
    """

    # reset multiindex
    df = _df.reset_index()

    # Keep only necessary columns
    df = df[[parameter, "timestamp"]]

    # Group by timestamp and take the sum of the parameter
    df = df.groupby("timestamp").sum().reset_index()

    # format timestamps
    format_timestamps(df)

    fig = px.line(
        df,
        x="timestamp",
        y=parameter,
        labels={
            "timestamp": "Time (hh:mm:ss)",
            parameter: f"{label} ({unit})",
        },
        title=f"Sum of {label} from all TECs",
        markers=True,
    )

    # set yaxis
    set_yaxis(fig_id=fig_id, fig=fig)

    # force the plot to always only have 2 ticks
    _force_two_ticks(fig, df)

    return fig


def update_graph_sum_power(df, fig_id):
    return update_graph_sum_generic(df, "output power", "Power", "W", fig_id)

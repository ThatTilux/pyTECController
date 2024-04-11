import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


def graphs():
    return html.Div(
        [
            dbc.Row(dbc.Col(html.Div(dcc.Graph(id="graph-object-temperature")))),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(dcc.Graph(id="graph-output-current")), width=12, md=6
                    ),  # 1 column only on md and smaller
                    dbc.Col(
                        html.Div(dcc.Graph(id="graph-output-voltage")), width=12, md=6
                    ),
                ]
            ),
        ]
    )


def format_timestamps(df):
    """
    Formats timestamps tp the hh:mm:ss format
    """
    df["timestamp"] = df["timestamp"].dt.strftime("%H:%M:%S")


def _force_two_ticks(fig, df):
    """
    Force the fig to have 2 ticks only, namely the two timestamps passed
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


def update_graph_object_temperature(df):

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


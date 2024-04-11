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
    df['timestamp'] = df['timestamp'].dt.strftime('%H:%M:%S')



def _force_two_ticks(fig, first_timestamp, last_timestamp):
    """
    Force the fig to have 2 ticks only, namely the two timestamps passed
    """
    fig.update_xaxes(
        tickmode='array',
        tickvals=[first_timestamp, last_timestamp],
        ticktext=[first_timestamp, last_timestamp]
    )


def update_graph_object_temperature(df):
    
    # Group by Plate and Timestamp, then calculate mean
    avg_temps = df.groupby(['Plate', 'timestamp'])["object temperature"].mean().reset_index()
    
    
    # reset multiindex
    temp_df = df.reset_index()

    
     # Extract the first target temperature for each Plate at each timestamp
    target_temps = temp_df.drop_duplicates(subset=['Plate', 'timestamp'])[['Plate', 'timestamp', 'target object temperature']]
    
    # Format the Timestamps to hh:mm:ss
    format_timestamps(avg_temps)
    format_timestamps(target_temps)
    
    # color map for all lines
    color_map = {"top": "red", "bottom": "blue"}

    
    fig = px.line(
        avg_temps,
        x="timestamp",
        y="object temperature",
        color="Plate",
        labels={
            "timestamp": "Time (hh:mm:ss)",
            "object temperature": "Temperature (°C)",
        },
        title="Average Plate Temperatures",
        markers=True,
        color_discrete_map=color_map
    )
    
    
    
    # Add lines for target object temperatures
    for plate in target_temps['Plate'].unique():
        plate_target_temps = target_temps[target_temps['Plate'] == plate]
        fig.add_trace(go.Scatter(
            x=plate_target_temps['timestamp'],
            y=plate_target_temps['target object temperature'],
            mode='lines',
            name=f"Target Temperature ({plate})",
            line=dict(color=color_map[plate], width=2, dash='dash'), 
            showlegend=False
        ))
    
    # force the plot to always only have 2 ticks
    
    if not avg_temps.empty:
        first_timestamp = avg_temps['timestamp'].iloc[0]
        last_timestamp = avg_temps['timestamp'].iloc[-1]
        _force_two_ticks(fig, first_timestamp, last_timestamp)

    
    return fig


def update_graph_output_current(df):
    # for the current, we have to take the max of 2 TECs connected to the same TEC controller
    # these values will be added up to get the total current drawn
    
    
    # Keep only necessary columns
    df_filtered = df[['output current', 'timestamp']]

    # Group by timestamp first
    grouped_by_timestamp = df_filtered.groupby('timestamp')

    results = []  

    for timestamp, group in grouped_by_timestamp:
        # Within each timestamp group, further group by Plate and TEC_ID pairs (0&1, 2&3, ...)
        grouped_by_plate_and_tec = group.groupby([group.index.get_level_values('Plate'), group.index.get_level_values('TEC_ID') // 2])

        # Find the max 'output current' within each group
        max_currents = grouped_by_plate_and_tec['output current'].max()

        # Sum the max currents for this timestamp
        total_current = max_currents.sum()

        # Append the result
        results.append({'timestamp': timestamp, 'output current': total_current})

    # Create a DataFrame from the results
    result_df = pd.DataFrame(results)
    
    # format timestamps 
    format_timestamps(result_df)
    
    
    fig = px.line(
        result_df,
        x="timestamp",
        y="output current",
        labels={
            "timestamp": "Time (hh:mm:ss)",
            "output current": "Current (A)",
        },
        title="Total Current Drawn (TODO)",
        markers=True
    )
    
    if not result_df.empty:
        first_timestamp = result_df['timestamp'].iloc[0]
        last_timestamp = result_df['timestamp'].iloc[-1]
        _force_two_ticks(fig, first_timestamp, last_timestamp)
    
    return fig
    
    
    
def update_graph_output_voltage(df):
    
    # Keep only necessary columns
    df = df[['output voltage', 'timestamp']]
    
    # Group by timestamp first
    grouped_by_timestamp = df.groupby('timestamp')
    
    # find max voltages
    max_voltages = grouped_by_timestamp['output voltage'].max().reset_index()
    
    # format timestamps 
    format_timestamps(max_voltages)
    
    fig = px.line(
        max_voltages,
        x="timestamp",
        y="output voltage",
        labels={
            "timestamp": "Time (hh:mm:ss)",
            "output voltage": "Voltage (V)",
        },
        title="Maximum Voltage Drawn by any TEC",
        markers=True
    )
    
    if not max_voltages.empty:
        first_timestamp = max_voltages['timestamp'].iloc[0]
        last_timestamp = max_voltages['timestamp'].iloc[-1]
        _force_two_ticks(fig, first_timestamp, last_timestamp)
    
    return fig

    
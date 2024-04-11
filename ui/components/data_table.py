from dash import dash_table


def data_table():
    return dash_table.DataTable(
            id="tec-data-table",
            style_data_conditional=[
                # Heating status - Red
                {
                    "if": {"filter_query": '{loop status} = "Heating"'},
                    "backgroundColor": "#FFA07A",
                    "color": "black",
                },
                # Cooling status - Blue
                {
                    "if": {"filter_query": '{loop status} = "Cooling"'},
                    "backgroundColor": "#ADD8E6",
                    "color": "black",
                },
                # Stable status - Green
                {
                    "if": {"filter_query": '{loop status} = "Stable"'},
                    "backgroundColor": "#90EE90",
                    "color": "black",
                },
            ],
            style_table={'overflowX': 'auto'},  # horizontal scrolling instead of overflow
        )
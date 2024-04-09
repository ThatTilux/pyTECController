from dash import dash_table,html, dcc

layout = html.Div([
    html.H1("TEC Data Display"),
    dash_table.DataTable(id='tec-data-table'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # 1s
        n_intervals=0
    )
])

import dash
from dash import html
from .layouts import layout

app = dash.Dash(__name__)
app.layout = layout


# Importing callbacks at the end to avoid circular imports
from .callbacks import register_callbacks
register_callbacks(app)



if __name__ == '__main__':
    app.run_server(debug=True)
import dash
from dash import html
import dash_bootstrap_components as dbc
from ui.layouts import layout


app = dash.Dash(
    __name__,
    title="TEC Controller",
    update_title=None,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.layout = layout


# Importing callbacks at the end to avoid circular imports
from .callbacks import register_callbacks

register_callbacks(app)


if __name__ == "__main__":
    app.run_server(debug=True)

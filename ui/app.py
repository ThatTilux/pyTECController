import os
import dash
from dash import html
import dash_bootstrap_components as dbc
from ui.layouts import layout


app = dash.Dash(
    __name__,
    title="TEC Controller",
    update_title=None,  # prevents the Updating... title
    external_stylesheets=[dbc.themes.BOOTSTRAP],  # use bootstrap default theme
)
app.layout = layout(app)


# Importing callbacks at the end to avoid circular imports
from .callbacks.callbacks import register_callbacks

register_callbacks(app)


if __name__ == "__main__":
    # disable the dev tools in a production environment
    debug = os.getenv("FLASK_ENV") == "development"

<<<<<<< HEAD
    app.run(debug=debug)
=======
    app.run_server(debug=debug)
>>>>>>> 38be49382130558460cd464eb41b93449d145c8d

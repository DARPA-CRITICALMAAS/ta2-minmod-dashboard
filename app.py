import dash_bootstrap_components as dbc
import dash
from dash import html
from flask import Flask
from constants import SPARQL_ENDPOINT
import sys

FA = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"

server = Flask(__name__)  # define flask app.server

app = dash.Dash(
    url_base_pathname="/dashboard/",
    external_stylesheets=[dbc.themes.LITERA, FA],
    use_pages=True,
    server=server,
)

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>MinMod</title>
        <link rel="icon" type="image/x-icon" href="/assets/favicon.png">
        {%css%}
    </head>
    <body style="display: flex; flex-direction: column; min-height: 100vh;">
        {%app_entry%}
        <footer style="margin-top: auto;">
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

app.layout = html.Div(
    style={"display": "flex", "flexDirection": "column", "minHeight": "100vh"},
    children=[
        html.Div(
            dash.page_container,
            style={
                "flex": "1 0 auto",  # Ensure it takes the remaining space but can grow
                # "margin-bottom": "40px",
            },
        ),
    ],
)

app.config.suppress_callback_exceptions = True

# Run app and display result inline in the notebook
if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050)

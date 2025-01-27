import dash
from dash import html, callback, clientside_callback, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import dash
from components import stats_card, pie_card, geo_model_card
from helpers import kpis
from models import GeoMineral
from helpers import sparql_utils
import time
from dash import callback_context
from dash.exceptions import PreventUpdate

dash.register_page(__name__, path="/mapview")

gm = GeoMineral(commodity="nickel")
gm.init()


def render():
    return html.Div(
        [
            dcc.Location(id="url-minmod", refresh=True),
            dbc.Row(),
            dbc.Row(
                [
                    dbc.Row(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        dbc.Row(html.H3("Map View")),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Spinner(
                                                        dcc.Dropdown(
                                                            id="commodity-main-geo",
                                                            options=[
                                                                {
                                                                    "label": commodity,
                                                                    "value": commodity,
                                                                }
                                                                for commodity in kpis.get_commodities()
                                                            ],
                                                            value="nickel",
                                                            placeholder="Search Commodity",
                                                            style={
                                                                "margin-bottom": "5px",
                                                                "margin-top": "20px",
                                                                "margin-left": "5px",
                                                            },
                                                        ),
                                                    ),
                                                    width=2,
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        html.I(
                                                            " Toggle Map View",
                                                            className="fas fa-sun",
                                                        ),
                                                        id="theme-toggle-button",
                                                        color="default",
                                                        className="mr-1",
                                                        style={
                                                            "border": "1px",
                                                            "margin-top": "20px",
                                                        },
                                                    ),
                                                    width=3,
                                                ),
                                            ],
                                            className="g-0",
                                        ),
                                        dbc.Spinner(
                                            html.Div(
                                                geo_model_card(gm, "light"),
                                                id="render-geo-plot",
                                            )
                                        ),
                                    ]
                                )
                            )
                        ],
                        style={"padding-left": "40px", "margin-top": "20px"},
                    ),
                ],
                align="start",
            ),
            html.Div(id="url-geo", style={"display": "none"}),
            # Dummy div to satisfy Dash callback requirements
            html.Div(id="url-div-geo", style={"display": "none"}),
        ]
    )


layout = render()


@callback(
    Output("commodity-main-geo", "options"),
    Input(
        "url-minmod", "pathname"
    ),  # This triggers the callback when the page is refreshed or the URL changes
)
def update_commodity_dropdown(pathname):
    options = [
        {"label": commodity, "value": commodity} for commodity in kpis.get_commodities()
    ]
    return options


@callback(Output("commodity-main-geo", "value"), Input("commodity-main-geo", "options"))
def set_default_commodity(options):
    return options[0]["value"] if options else None


@callback(
    Output("url-geo", "children"),
    Output("clickable-geo-plot", "clickData"),
    Input("clickable-geo-plot", "clickData"),
    prevent_initial_call=True,
)
def open_url(clickData):
    """A callback to handle geo map plot based on the user click"""
    if clickData:
        clicked_dict = clickData["points"][0]
        filtered_df = gm.df[
            (gm.df["lat"] == clicked_dict["lat"])
            & (gm.df["lon"] == clicked_dict["lon"])
        ]
        return filtered_df["ms"].tolist()[0], None
    return None, None


@callback(
    [Output("theme-toggle-button", "children"), Output("render-geo-plot", "children")],
    [Input("theme-toggle-button", "n_clicks"), Input("commodity-main-geo", "value")],
    [
        State("theme-toggle-button", "children"),
        State("render-geo-plot", "children"),
        State("theme-toggle-button", "n_clicks"),
    ],
)
def update_ui(n_clicks_theme, selected_commodity, current_icon, _, n_clicks_previous):
    """A callback to handle map theme and render map based on the commodity selected"""
    # Initial state when no button has been clicked yet
    if n_clicks_theme is None:
        n_clicks_theme = 0
    if n_clicks_previous is None:
        n_clicks_previous = 0

    trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]

    # Determine current theme based on button click count
    if trigger_id == "theme-toggle-button":
        # Toggle theme based on the count of button clicks
        is_dark = n_clicks_theme % 2 == 1
        new_theme = "dark" if is_dark else "light"
        new_class = "fas fa-moon" if is_dark else "fas fa-sun"
        return [
            html.I(" Toggle Map View", className=new_class),
            geo_model_card(gm, new_theme),
        ]
    elif trigger_id == "commodity-main-geo":
        # Maintain the theme based on the last button click count
        is_dark = n_clicks_previous % 2 == 1
        current_theme = "dark" if is_dark else "light"
        if selected_commodity == gm.commodity:
            return [current_icon, geo_model_card(gm, current_theme)]
        selected_commodity = selected_commodity.split()[0]
        gm.update_commodity(selected_commodity)
        gm.init()
        return [current_icon, geo_model_card(gm, current_theme)]
    else:
        raise PreventUpdate


# Clientside function to open a new tab
clientside_callback(
    """
    function(url) {
        if(url) {
            window.open(url);
        }
    }
    """,
    Output("url-div-geo", "children"),  # Dummy output, we don't use it
    [Input("url-geo", "children")],  # Input is the URL to open
)

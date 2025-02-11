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

dash.register_page(__name__, path="/")

mineral_inventories = kpis.get_mineral_inventories_count_by_commodity()


def render():
    return html.Div(
        [
            dcc.Location(id="url-minmod", refresh=True),
            dbc.Row(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Row(
                                    [
                                        dbc.Row(
                                            dbc.Card(
                                                html.Div(
                                                    [
                                                        html.H3(
                                                            ["Number of Mineral Sites"]
                                                        ),
                                                        dbc.Spinner(
                                                            html.H4(
                                                                ["empty"],
                                                                id="mineral-sites-count-card",
                                                            ),
                                                        ),
                                                    ],
                                                    className=f"border-sucess border-start border-5",
                                                ),
                                                className="text-center text-nowrap my-2 p-2",
                                            )
                                        ),
                                        dbc.Row(
                                            dbc.Spinner(
                                                html.Div(
                                                    html.Div(
                                                        style={"margin-top": "50px"}
                                                    ),
                                                    id="pie--card--min",
                                                ),
                                            )
                                        ),
                                    ]
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                dbc.Row(
                                    [
                                        dbc.Row(
                                            dbc.Card(
                                                html.Div(
                                                    [
                                                        html.H3(
                                                            ["Number of Inventories"]
                                                        ),
                                                        dbc.Spinner(
                                                            html.H4(
                                                                ["empty"],
                                                                id="inventory-count-card",
                                                            ),
                                                        ),
                                                    ],
                                                    className=f"border-sucess border-start border-5",
                                                ),
                                                className="text-center text-nowrap my-2 p-2",
                                            )
                                        ),
                                        dbc.Row(
                                            dbc.Spinner(
                                                html.Div(
                                                    html.Div(
                                                        style={"margin-top": "50px"}
                                                    ),
                                                    id="pie--card",
                                                ),
                                            )
                                        ),
                                    ]
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                dbc.Row(
                                    [
                                        dbc.Row(
                                            dbc.Card(
                                                html.Div(
                                                    [
                                                        html.H3(
                                                            ["Number of Documents"]
                                                        ),
                                                        dbc.Spinner(
                                                            html.H4(
                                                                ["empty"],
                                                                id="documents-count-card",
                                                            ),
                                                        ),
                                                    ],
                                                    className=f"border-sucess border-start border-5",
                                                ),
                                                className="text-center text-nowrap my-2 p-2",
                                            )
                                        ),
                                        dbc.Row(
                                            dbc.Spinner(
                                                html.Div(
                                                    html.Div(
                                                        style={"margin-top": "50px"}
                                                    ),
                                                    id="pie--card--docs",
                                                ),
                                            )
                                        ),
                                    ]
                                ),
                                width=4,
                            ),
                        ],
                    ),
                ]
            ),
            dcc.Interval(
                id="interval-component",
                interval=12
                * 60
                * 60
                * 1000,  # Trigger refresh every 12 hours; adjust as needed
                n_intervals=0,
            ),
            html.Div(id="url-geo", style={"display": "none"}),
            # Dummy div to satisfy Dash callback requirements
            html.Div(id="url-div-geo", style={"display": "none"}),
        ]
    )


layout = render()


@callback(
    [Output("documents-count-card", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_all_cards(_):
    """A callback to handle all the KPI card updates"""
    return ["{:,}".format(kpis.get_documents_count())]


@callback(
    [Output("inventory-count-card", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_all_cards(_):
    """A callback to handle the KPI card updates"""
    return ["{:,}".format(kpis.get_inventory_count())]


@callback(
    [Output("mineral-sites-count-card", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_all_cards(_):
    """A callback to handle the KPI card updates"""
    return ["{:,}".format(kpis.get_mineral_site_count())]


@callback(
    [Output("pie--card--min", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_all_cards(_):
    """A callback to handle the PI chart updates"""
    ms_per_commodity = kpis.get_mineral_site_count_per_commodity()
    return [
        html.Div(
            pie_card(
                ms_per_commodity["labels"],
                ms_per_commodity["values"],
                "Mineral Site Distribution By Commodity",
            ),
        )
    ]


@callback(
    [Output("pie--card--docs", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_all_cards(_):
    """A callback to handle the PI chart updates"""
    docs_per_commodity = kpis.get_docs_per_commodity()
    return [
        html.Div(
            pie_card(
                docs_per_commodity["labels"],
                docs_per_commodity["values"],
                "Document Distribution By Commodity",
            )
        )
    ]


@callback(
    Output("commodity-main", "options"),
    Input(
        "url-minmod", "pathname"
    ),  # This triggers the callback when the page is refreshed or the URL changes
)
def update_commodity_dropdown(pathname):
    options = [
        {"label": commodity, "value": commodity} for commodity in kpis.get_commodities()
    ]
    return options


@callback(Output("commodity-main", "value"), Input("commodity-main", "options"))
def set_default_commodity(options):
    return options[0]["value"] if options else None


@callback(
    [Output("pie--card", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_all_cards(_):
    """A callback to handle the PI chart updates"""
    mineral_inventories = kpis.get_mineral_inventories_count_by_commodity()
    return [
        html.Div(
            pie_card(
                mineral_inventories["labels"],
                mineral_inventories["values"],
                "Inventory Distribution By Commodity",
            )
        )
    ]

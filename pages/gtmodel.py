import dash
from dash import html, callback, clientside_callback, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import json

from helpers import kpis
from components import get_gt_model
from models import GradeTonnage
from helpers.exceptions import MinModException
from constants import ree_minerals, heavy_ree_minerals, light_ree_minerals, pge_minerals

dash.register_page(__name__, path="/gtmodel")

layout = html.Div(
    style={
        "display": "flex",
        "flexDirection": "column",
        "minHeight": "100vh",
    },
    children=[
        dcc.Location(id="url-gt", refresh=True),
        dbc.Card(
            dbc.CardBody(
                [
                    # ------------------------ Commodity + Generate row ------------------------
                    dbc.Row(
                        dbc.Col(
                            [
                                html.P(
                                    "Select Commodity",
                                    style={
                                        "font-family": '"Open Sans", verdana, arial, sans-serif',
                                        "font-size": "15px",
                                        "text-align": "center",
                                        "font-weight": "bold",
                                    },
                                ),
                                dbc.InputGroup(
                                    [
                                        dcc.Dropdown(
                                            id="commodity-gt",
                                            # The options will be updated by the callback 'update_commodity_dropdown'
                                            options=[],
                                            multi=True,
                                            placeholder="Search Commodity",
                                            style={
                                                "width": "300px",
                                                "fontSize": "13px",
                                            },
                                        ),
                                        dbc.Button(
                                            "Generate",
                                            id="generate-btn",
                                            color="primary",
                                            style={
                                                "fontSize": "13px",
                                            },
                                        ),
                                    ],
                                    style={"justifyContent": "center"},
                                ),
                            ],
                            width=6,
                            style={
                                "padding": "20px 0",
                                "margin": "auto",
                                "text-align": "center",
                            },
                        ),
                        style={
                            "margin-top": "15px",
                            "margin-bottom": "30px",
                        },
                    ),
                    # ------------------------ Figure row ------------------------
                    dbc.Row(
                        [
                            dbc.Spinner(
                                html.Div(
                                    [
                                        dcc.Graph(
                                            id="clickable-plot",
                                            figure={},
                                            style={"display": "none"},
                                        )
                                    ],
                                    id="render-plot",
                                ),
                                size="lg",
                                spinner_style={"width": "4rem", "height": "4rem"},
                            ),
                        ],
                        className="my-2",
                    ),
                    # ------------------------ Aggregation + Download row ------------------------
                    html.Div(
                        id="slider-download-container",
                        children=[
                            dbc.Row(
                                [
                                    # Left Column with label and InputGroup (Input + Button)
                                    dbc.Col(
                                        [
                                            html.P(
                                                "Geo Spatial Aggregation (Kilometers)",
                                                style={
                                                    "font-family": '"Open Sans", verdana, arial, sans-serif',
                                                    "font-size": "15px",
                                                    "text-align": "center",
                                                    "font-weight": "bold",
                                                },
                                            ),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="aggregation-input",
                                                        type="number",
                                                        value=0,  # Default value
                                                        step=0.1,
                                                        style={
                                                            "maxWidth": "200px",
                                                            "font-size": "13px",
                                                        },
                                                    ),
                                                    dbc.Button(
                                                        "Aggregate",
                                                        id="aggregate-btn",
                                                        color="primary",
                                                    ),
                                                ],
                                                style={"justifyContent": "center"},
                                            ),
                                        ],
                                        width=6,
                                        style={
                                            "padding": "20px 0",
                                            "margin": "auto",
                                            "text-align": "center",
                                        },
                                    ),
                                    # Right Column with Download CSV button
                                    dbc.Col(
                                        dbc.Button(
                                            "Download CSV",
                                            id="download-btn",
                                            color="primary",
                                        ),
                                        width="auto",
                                        style={
                                            "text-align": "right",
                                            "padding-top": "20px",
                                        },
                                        className="d-flex justify-content-end",
                                    ),
                                ],
                                className="my-3 d-flex justify-content-between align-items-center",
                            )
                        ],
                    ),
                    dcc.Download(id="download-csv"),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "height": "auto",
                },
            ),
            style={
                "margin": "10px",
                "margin-top": "30px",
                "display": "flex",
                "flex-direction": "column",
            },
        ),
        dcc.Store(id="gt-agg-data"),
        dcc.Store(id="gt-df-data"),
        dcc.Store(id="select-commodity-data"),
        html.Div(id="url", style={"display": "none"}),
        html.Div(id="url-div", style={"display": "none"}),
    ],
)


@callback(
    Output("commodity-gt", "options"),
    Input("url-gt", "pathname"),
)
def update_commodity_dropdown(pathname):
    """
    Update the commodity dropdown options whenever this page loads or refreshes.
    """
    options = [
        {"label": commodity, "value": commodity} for commodity in kpis.get_commodities()
    ]
    return options


@callback(
    Output("slider-download-container", "style"),
    Input("clickable-plot", "figure"),
)
def toggle_slider_and_download(figure):
    """
    Show or hide the aggregation + download container based on whether the figure has data.
    """
    if figure and figure.get("data"):
        return {"display": "block"}
    return {"display": "none"}


@callback(
    [
        Output("gt-agg-data", "agg_data"),
        Output("gt-df-data", "df_data"),
        Output("select-commodity-data", "commodity_data"),
        Output("render-plot", "children"),
        Output("commodity-gt", "value"),
    ],
    [
        Input("generate-btn", "n_clicks"),  # Trigger on "Generate" button
        Input("aggregate-btn", "n_clicks"),  # Trigger on "Aggregate" button
    ],
    [
        State("commodity-gt", "value"),  # Dropdown commodities as State
        State("aggregation-input", "value"),  # The proximity value
        State("clickable-plot", "figure"),  # Current figure
    ],
    prevent_initial_call=True,
)
def update_output(
    generate_n_clicks,
    aggregate_n_clicks,
    selected_commodities,
    user_proximity_value,
    figure,
):
    """
    Render the Grade-Tonnage model based on:
      - The selected commodities (via State)
      - The proximity value (if "Aggregate" is clicked)
      - The triggered button (either 'Generate' or 'Aggregate')
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if not selected_commodities:
        # If no commodity is selected, reset the figure
        return (
            None,
            None,
            None,
            [
                dcc.Graph(
                    id="clickable-plot",
                    figure={},
                    style={"display": "none"},
                ),
            ],
            [],
        )

    # Default proximity value = 0 unless user clicked Aggregate
    proximity_value = 0
    if triggered_id == "aggregate-btn":
        proximity_value = user_proximity_value or 0

    # Expand custom REE groupings
    if "REE" in selected_commodities:
        selected_commodities.remove("REE")
        selected_commodities = list(set(selected_commodities + ree_minerals))

    if "HEAVY-REE" in selected_commodities:
        selected_commodities.remove("HEAVY-REE")
        selected_commodities = list(set(selected_commodities + heavy_ree_minerals))

    if "LIGHT-REE" in selected_commodities:
        selected_commodities.remove("LIGHT-REE")
        selected_commodities = list(set(selected_commodities + light_ree_minerals))

    if "PGE" in selected_commodities:
        selected_commodities.remove("PGE")
        selected_commodities = list(set(selected_commodities + pge_minerals))

    try:
        gt = GradeTonnage(selected_commodities, proximity_value)
        gt.init()

        # Preserve visibility from the existing figure if the user just clicked Aggregate
        if triggered_id == "aggregate-btn" and figure and "data" in figure:
            visible_traces = [
                " ".join(trace["name"].split()[:-1])
                for trace in figure["data"]
                if "hovertemplate" in trace and trace.get("visible", True) is True
            ]
            gt.visible_traces = visible_traces

    except MinModException as e:
        # Handle custom exception
        return (
            None,
            None,
            selected_commodities,
            [
                dbc.Alert(str(e), color="danger"),
                dcc.Graph(id="clickable-plot", figure={}, style={"display": "none"}),
            ],
            selected_commodities,
        )
    except Exception:
        # Handle generic error
        return (
            None,
            None,
            selected_commodities,
            [
                dbc.Alert(
                    "No results found or there was an error with the query.",
                    color="danger",
                ),
                dcc.Graph(id="clickable-plot", figure={}, style={"display": "none"}),
            ],
            selected_commodities,
        )

    # Build the GT model figure
    gt, gt_model_plot = get_gt_model(gt, proximity_value)

    return (
        json.dumps(
            [df.to_json(date_format="iso", orient="split") for df in gt.aggregated_df]
        ),
        gt.df.to_json(date_format="iso", orient="split"),
        selected_commodities,
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        dcc.Graph(
                            id="clickable-plot",
                            figure=gt_model_plot,
                            config={
                                "displayModeBar": True,
                                "displaylogo": False,
                                "responsive": True,
                                "showTips": True,
                                "scrollZoom": True,
                                "modeBarButtonsToRemove": [
                                    "autoScale2d",
                                    "lasso2d",
                                    "select2d",
                                    "zoomIn2d",
                                    "zoomOut2d",
                                ],
                            },
                        )
                    ]
                )
            )
        ],
        selected_commodities,
    )


@callback(
    Output("url", "children"),
    Output("clickable-plot", "clickData"),
    Input("clickable-plot", "clickData"),
    State("gt-df-data", "df_data"),
    prevent_initial_call=True,
)
def open_url(clickData, df_data):
    """
    A callback to open the clicked ms url on a new tab.
    Resets clickData so repeated clicks on the same point still trigger.
    """
    if not df_data:
        raise dash.exceptions.PreventUpdate
    df_data = pd.read_json(df_data, orient="split")
    if clickData:
        filtered_df = df_data[df_data["ms_name"] == clickData["points"][0]["text"]]
        return filtered_df["ms"].tolist()[0], None
    return None, None


# Clientside function to open a new tab
clientside_callback(
    """
    function(url) {
        if(url) {
            window.open(url);
        }
    }
    """,
    Output("url-div", "children"),
    [Input("url", "children")],
)


@callback(
    Output("download-csv", "data"),
    Input("download-btn", "n_clicks"),
    [
        State("gt-agg-data", "agg_data"),
        State("clickable-plot", "figure"),
    ],
    prevent_initial_call=True,
)
def download_csv(n_clicks, agg_data, figure):
    """
    Callback to generate CSV data for download only when the button is clicked.
    """
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    if not agg_data or not figure:
        raise dash.exceptions.PreventUpdate

    try:
        aggregated_df = [
            pd.read_json(dt, orient="split") for dt in json.loads(agg_data)
        ]
        df = pd.concat(aggregated_df, ignore_index=True)[
            [
                "ms",
                "ms_name",
                "commodity",
                "top1_deposit_name",
                "lat",
                "lon",
                "total_tonnage",
                "total_grade",
            ]
        ].copy()

        column_names = [
            "Mineral Site URL",
            "Mineral Site Name",
            "Commodity",
            "Deposit Name",
            "Latitude",
            "Longitude",
            "Total Tonnage(Million tonnes)",
            "Total Grade(Percent)",
        ]

        # Only keep data corresponding to visible traces
        visible_traces = [
            " ".join(trace["name"].split()[:-1])
            for trace in figure["data"]
            if "hovertemplate" in trace and trace.get("visible", True) is True
        ]
        df = df[df["top1_deposit_name"].isin(visible_traces)]

        # Clean up text
        df["ms_name"] = df["ms_name"].apply(
            lambda x: x[2:].replace("::", ",") if "::" in x else x
        )
        df["ms"] = df["ms"].apply(
            lambda x: x[2:].replace("::", ",") if "::" in x else x
        )

        df.columns = column_names

        if df.empty:
            print("No data available to download.")
            raise dash.exceptions.PreventUpdate

        return dcc.send_data_frame(df.to_csv, "gt_data.csv")
    except Exception as e:
        print(f"Error generating CSV: {e}")
        raise dash.exceptions.PreventUpdate

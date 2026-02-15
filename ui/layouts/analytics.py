from dash import html, dcc
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H3("Analytics & Trends", className="mb-4"),

        # Moving averages
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Spending Trends with Moving Averages"),
                    dbc.CardBody(dcc.Graph(id="moving-avg-chart")),
                ], className="shadow-sm"),
            ], md=12),
        ], className="mb-4"),

        # Anomalies and growth rates
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Spending Anomalies"),
                    dbc.CardBody(id="anomalies-body"),
                ], className="shadow-sm"),
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Category Growth Rates"),
                    dbc.CardBody(dcc.Graph(id="growth-rates-chart")),
                ], className="shadow-sm"),
            ], md=6),
        ], className="mb-4"),

        # Seasonal patterns
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Seasonal Spending Patterns"),
                    dbc.CardBody(dcc.Graph(id="seasonal-chart")),
                ], className="shadow-sm"),
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Category Breakdown Over Time"),
                    dbc.CardBody(dcc.Graph(id="category-time-chart")),
                ], className="shadow-sm"),
            ], md=6),
        ]),
    ])

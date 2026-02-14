from dash import html, dcc
import dash_bootstrap_components as dbc


def summary_card(title, value, icon, color):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"fas {icon} fa-2x", style={"color": color}),
                ], className="me-3"),
                html.Div([
                    html.P(title, className="text-muted mb-1", style={"fontSize": "0.85rem"}),
                    html.H4(value, className="mb-0 fw-bold"),
                ]),
            ], className="d-flex align-items-center"),
        ]),
        className="shadow-sm mb-3",
    )


def layout():
    return html.Div([
        html.H3("Dashboard", className="mb-4"),

        # Summary Cards
        dbc.Row(id="summary-cards", className="mb-4"),

        # Charts Row 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Monthly Income vs Expenses vs Savings"),
                    dbc.CardBody(dcc.Graph(id="monthly-trend-chart")),
                ], className="shadow-sm"),
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Expense Breakdown"),
                    dbc.CardBody(dcc.Graph(id="expense-pie-chart")),
                ], className="shadow-sm"),
            ], md=4),
        ], className="mb-4"),

        # Charts Row 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Savings Rate Trend"),
                    dbc.CardBody(dcc.Graph(id="savings-rate-chart")),
                ], className="shadow-sm"),
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Daily Spending Heatmap"),
                    dbc.CardBody(dcc.Graph(id="spending-heatmap")),
                ], className="shadow-sm"),
            ], md=6),
        ], className="mb-4"),

        # Forecast card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Next Month Forecast"),
                    dbc.CardBody(id="forecast-card-body"),
                ], className="shadow-sm"),
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Budget Status"),
                    dbc.CardBody(id="budget-status-body"),
                ], className="shadow-sm"),
            ], md=6),
        ]),

        # Hidden interval for auto-refresh
        dcc.Interval(id="dashboard-refresh", interval=30000, n_intervals=0),
    ])

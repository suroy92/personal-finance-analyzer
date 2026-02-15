from dash import html, dcc
import dash_bootstrap_components as dbc

from models.keywords import ALL_EXPENSE_CATEGORIES


def layout():
    return html.Div([
        html.H3("Savings Suggestions", className="mb-4"),

        # Personalized suggestions
        dbc.Card([
            dbc.CardHeader("Personalized Recommendations"),
            dbc.CardBody(id="suggestions-body"),
        ], className="shadow-sm mb-4"),

        # What-if calculator
        dbc.Card([
            dbc.CardHeader("What-If Calculator"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Category"),
                        dbc.Select(
                            id="whatif-category",
                            options=[{"label": c, "value": c} for c in ALL_EXPENSE_CATEGORIES],
                        ),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Reduce spending by (%)"),
                        dbc.Input(id="whatif-pct", type="number", value=20, min=1, max=100),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("\u00a0"),
                        dbc.Button("Calculate", id="whatif-btn", color="primary"),
                    ], md=2),
                    dbc.Col(id="whatif-result", md=3),
                ]),
            ]),
        ], className="shadow-sm mb-4"),

        # Subscription audit
        dbc.Card([
            dbc.CardHeader("Subscription Audit"),
            dbc.CardBody(id="subscription-audit-body"),
        ], className="shadow-sm mb-4"),

        # Top discretionary spending
        dbc.Card([
            dbc.CardHeader("Top Discretionary Spending"),
            dbc.CardBody(dcc.Graph(id="discretionary-chart")),
        ], className="shadow-sm"),
    ])

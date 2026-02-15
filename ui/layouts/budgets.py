from dash import html, dcc
import dash_bootstrap_components as dbc

from models.keywords import ALL_EXPENSE_CATEGORIES, ALL_SAVINGS_CATEGORIES


def layout():
    all_categories = ALL_EXPENSE_CATEGORIES + ALL_SAVINGS_CATEGORIES

    return html.Div([
        html.H3("Budget Management", className="mb-4"),

        # Set budget form
        dbc.Card([
            dbc.CardHeader("Set Monthly Budget"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Category"),
                        dbc.Select(
                            id="budget-category",
                            options=[{"label": c, "value": c} for c in all_categories],
                        ),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Monthly Limit"),
                        dbc.Input(id="budget-amount", type="number", min=0, step=100),
                    ], md=4),
                    dbc.Col([
                        dbc.Label("\u00a0"),
                        html.Div([
                            dbc.Button("Set Budget", id="set-budget-btn", color="primary", className="me-2"),
                            dbc.Button("Apply 50/30/20 Rule", id="apply-rule-btn", color="info"),
                        ]),
                    ], md=4),
                ]),
                html.Div(id="budget-set-feedback", className="mt-2"),
            ]),
        ], className="shadow-sm mb-4"),

        # Budget vs Actual
        dbc.Card([
            dbc.CardHeader([
                "Budget vs Actual Spending",
                dbc.Select(
                    id="budget-month-select",
                    options=[],
                    className="d-inline-block ms-3",
                    style={"width": "200px"},
                ),
            ], className="d-flex align-items-center"),
            dbc.CardBody([
                dcc.Graph(id="budget-vs-actual-chart"),
                html.Div(id="budget-details-table"),
            ]),
        ], className="shadow-sm mb-4"),

        # 50/30/20 Analysis
        dbc.Card([
            dbc.CardHeader("50/30/20 Rule Analysis"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(dcc.Graph(id="rule-analysis-chart"), md=6),
                    dbc.Col(id="rule-analysis-details", md=6),
                ]),
            ]),
        ], className="shadow-sm"),
    ])

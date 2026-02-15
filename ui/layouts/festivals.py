from dash import html, dcc
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H3("Festival Alerts & Planning", className="mb-4"),

        # Upcoming festivals
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-bell me-2"),
                "Upcoming Festivals",
            ]),
            dbc.CardBody(id="upcoming-festivals-body"),
        ], className="shadow-sm mb-4"),

        # Festive vs normal spending
        dbc.Card([
            dbc.CardHeader("Festive vs Normal Month Spending"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(dcc.Graph(id="festive-comparison-chart"), md=6),
                    dbc.Col(id="festive-stats-body", md=6),
                ]),
            ]),
        ], className="shadow-sm mb-4"),

        # Manage festivals
        dbc.Card([
            dbc.CardHeader("Manage Festival Calendar"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Festival Name"),
                        dbc.Input(id="new-festival-name", type="text", placeholder="e.g., Pongal"),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Month"),
                        dbc.Input(id="new-festival-month", type="number", min=1, max=12),
                    ], md=2),
                    dbc.Col([
                        dbc.Label("Day"),
                        dbc.Input(id="new-festival-day", type="number", min=1, max=31),
                    ], md=2),
                    dbc.Col([
                        dbc.Label("Duration (days)"),
                        dbc.Input(id="new-festival-duration", type="number", min=1, max=30, value=1),
                    ], md=2),
                    dbc.Col([
                        dbc.Label("\u00a0"),
                        dbc.Button("Add Festival", id="add-festival-btn", color="primary"),
                    ], md=3),
                ]),
                html.Div(id="add-festival-feedback", className="mt-2"),
                html.Hr(),
                html.Div(id="festival-list-body"),
            ]),
        ], className="shadow-sm"),
    ])

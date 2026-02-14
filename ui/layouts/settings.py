from dash import html, dcc
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H3("Settings", className="mb-4"),

        dbc.Card([
            dbc.CardHeader("ML Model Management"),
            dbc.CardBody([
                dbc.Button(
                    [html.I(className="fas fa-sync me-2"), "Retrain Models Now"],
                    id="retrain-btn", color="warning",
                ),
                html.Div(id="retrain-feedback", className="mt-2"),
            ]),
        ], className="shadow-sm mb-4"),

        dbc.Card([
            dbc.CardHeader("Database"),
            dbc.CardBody([
                dbc.Button(
                    [html.I(className="fas fa-download me-2"), "Backup Database"],
                    id="backup-db-btn", color="info", className="me-2",
                ),
                dcc.Download(id="download-backup"),
                html.Div(id="backup-feedback", className="mt-2"),
            ]),
        ], className="shadow-sm"),
    ])

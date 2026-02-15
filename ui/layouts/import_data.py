from dash import html, dcc
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H3("Import Data", className="mb-4"),

        dbc.Card([
            dbc.CardHeader("Upload Bank Statement (CSV)"),
            dbc.CardBody([
                html.P(
                    "Upload a CSV file with columns: Date, Narration, Debit Amount, Credit Amount",
                    className="text-muted",
                ),
                dcc.Upload(
                    id="csv-upload",
                    children=html.Div([
                        html.I(className="fas fa-cloud-upload-alt fa-3x mb-3"),
                        html.Br(),
                        "Drag and Drop or ",
                        html.A("Click to Select", className="text-primary fw-bold"),
                        html.Br(),
                        html.Small("Supported formats: .csv", className="text-muted"),
                    ]),
                    style={
                        "width": "100%",
                        "height": "200px",
                        "lineHeight": "60px",
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "10px",
                        "borderColor": "#aaa",
                        "textAlign": "center",
                        "padding": "40px",
                        "cursor": "pointer",
                    },
                    multiple=False,
                ),
                html.Div(id="upload-feedback", className="mt-3"),
            ]),
        ], className="shadow-sm mb-4"),

        # Export section
        dbc.Card([
            dbc.CardHeader("Export Data"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-file-csv me-2"), "Export as CSV"],
                            id="export-csv-btn", color="success", className="me-2",
                        ),
                        dcc.Download(id="download-csv"),
                    ], md=4),
                ]),
            ]),
        ], className="shadow-sm"),
    ])

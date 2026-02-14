import base64
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

from ui.app import app
from services.transaction_service import get_all_transactions, ingest_csv


@app.callback(
    Output("transactions-table", "data"),
    Output("txn-count-info", "children"),
    Input("txn-type-filter", "value"),
    Input("txn-search", "value"),
    Input("txn-month-filter", "value"),
    Input("url", "pathname"),
)
def update_transactions_table(type_filter, search, month_filter, pathname):
    if pathname != "/transactions":
        return [], ""

    txns = get_all_transactions(limit=1000)

    if type_filter and type_filter != "all":
        txns = [t for t in txns if t["transaction_type"] == type_filter]

    if search:
        search_lower = search.lower()
        txns = [t for t in txns if search_lower in t["description"].lower()]

    if month_filter:
        txns = [t for t in txns if t["date"].startswith(month_filter)]

    return txns, f"Showing {len(txns)} transactions"


@app.callback(
    Output("upload-feedback", "children"),
    Input("csv-upload", "contents"),
    State("csv-upload", "filename"),
)
def handle_csv_upload(contents, filename):
    if contents is None:
        return ""

    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        result = ingest_csv(decoded, filename)

        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            html.Strong("Upload Successful! "),
            f"Processed {result['total_rows']} rows: "
            f"{result['inserted']} inserted, {result['skipped']} skipped (duplicates). "
            f"{len(result['uncategorized'])} need manual categorization.",
        ], color="success")

    except ValueError as e:
        return dbc.Alert([html.I(className="fas fa-exclamation-circle me-2"), str(e)], color="danger")
    except Exception as e:
        return dbc.Alert([html.I(className="fas fa-exclamation-circle me-2"), f"Error: {e}"], color="danger")


@app.callback(
    Output("download-csv", "data"),
    Input("export-csv-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_csv(n_clicks):
    import pandas as pd
    txns = get_all_transactions(limit=10000)
    if not txns:
        return None
    df = pd.DataFrame(txns)
    return dict(content=df.to_csv(index=False), filename="transactions_export.csv")

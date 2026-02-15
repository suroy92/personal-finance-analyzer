import base64
import threading
from dash import Input, Output, State, html, ctx, no_update
import dash_bootstrap_components as dbc

from ui.app import app
from services.transaction_service import (
    get_all_transactions,
    get_uncategorized_transactions,
    update_transaction_category,
    ingest_csv,
)
from models.keywords import (
    ALL_EXPENSE_CATEGORIES,
    ALL_SAVINGS_CATEGORIES,
    ALL_INCOME_CATEGORIES,
)
from models.ml_models import train_models
from core.config import get_config


def _currency():
    return get_config().get("currency", {}).get("symbol", "\u20B9")


# ───────────────────────────────────────────
# Transaction table
# ───────────────────────────────────────────
@app.callback(
    Output("transactions-table", "data"),
    Output("txn-count-info", "children"),
    Input("txn-type-filter", "value"),
    Input("txn-search", "value"),
    Input("txn-month-filter", "value"),
    Input("txn-category-filter", "value"),
    Input("category-save-trigger", "data"),
    Input("url", "pathname"),
)
def update_transactions_table(type_filter, search, month_filter, cat_filter, _save_trigger, pathname):
    if pathname != "/transactions":
        return [], ""

    txns = get_all_transactions(limit=1000)

    if type_filter and type_filter != "all":
        txns = [t for t in txns if t["transaction_type"] == type_filter]

    if cat_filter and cat_filter != "all":
        if cat_filter == "_uncategorized":
            txns = [t for t in txns if not t.get("category")]
        else:
            txns = [t for t in txns if t.get("category") == cat_filter]

    if search:
        search_lower = search.lower()
        txns = [t for t in txns if search_lower in t["description"].lower()]

    if month_filter:
        txns = [t for t in txns if t["date"].startswith(month_filter)]

    uncat_count = sum(1 for t in get_all_transactions(limit=5000) if not t.get("category"))
    info = f"Showing {len(txns)} transactions"
    if uncat_count > 0:
        info += f" | {uncat_count} uncategorized"

    return txns, info


# ───────────────────────────────────────────
# Row click → open edit modal
# ───────────────────────────────────────────
@app.callback(
    Output("edit-category-modal", "is_open"),
    Output("edit-txn-details", "children"),
    Output("selected-txn-hash", "data"),
    Output("edit-txn-type", "value"),
    Input("transactions-table", "selected_rows"),
    Input("cancel-edit-btn", "n_clicks"),
    Input("save-category-btn", "n_clicks"),
    State("transactions-table", "data"),
    State("edit-category-modal", "is_open"),
    prevent_initial_call=True,
)
def handle_row_select(selected_rows, cancel_clicks, save_clicks, table_data, is_open):
    trigger = ctx.triggered_id

    if trigger in ("cancel-edit-btn", "save-category-btn"):
        return False, no_update, no_update, no_update

    if not selected_rows or not table_data:
        return False, "", None, None

    row = table_data[selected_rows[0]]
    sym = _currency()

    # Pre-select type based on current transaction
    if row.get("is_saving"):
        preset_type = "Savings/Investment"
    elif row["transaction_type"] == "Credit":
        preset_type = "Income"
    else:
        preset_type = "Expense"

    details = html.Div([
        html.P([html.Strong("Date: "), row["date"]]),
        html.P([html.Strong("Description: "), row["description"]]),
        html.P([html.Strong("Amount: "), f"{sym}{row['amount']:,.2f}"]),
        html.P([html.Strong("Type: "), row["transaction_type"]]),
        html.P([
            html.Strong("Current Category: "),
            html.Span(
                row.get("category") or "None (uncategorized)",
                className="text-danger fw-bold" if not row.get("category") else "",
            ),
        ]),
    ])

    return True, details, row.get("hash"), preset_type


# ───────────────────────────────────────────
# Type selector → update category dropdown
# ───────────────────────────────────────────
@app.callback(
    Output("edit-txn-category", "options"),
    Output("edit-txn-category", "value"),
    Input("edit-txn-type", "value"),
)
def update_category_options(txn_type):
    if txn_type == "Income":
        options = [{"label": c, "value": c} for c in ALL_INCOME_CATEGORIES]
    elif txn_type == "Savings/Investment":
        options = [{"label": c, "value": c} for c in ALL_SAVINGS_CATEGORIES]
    else:
        options = [{"label": c, "value": c} for c in ALL_EXPENSE_CATEGORIES]

    return options, options[0]["value"] if options else None


# ───────────────────────────────────────────
# Save category
# ───────────────────────────────────────────
@app.callback(
    Output("edit-feedback", "children"),
    Output("category-save-trigger", "data"),
    Input("save-category-btn", "n_clicks"),
    State("selected-txn-hash", "data"),
    State("edit-txn-type", "value"),
    State("edit-txn-category", "value"),
    prevent_initial_call=True,
)
def save_category(n_clicks, txn_hash, txn_type, category):
    if not txn_hash or not category:
        return dbc.Alert("No transaction selected.", color="warning"), no_update

    is_saving = 1 if txn_type == "Savings/Investment" else 0
    update_transaction_category(txn_hash, category, is_saving)

    # Retrain in background so the model learns this correction
    threading.Thread(target=train_models, daemon=True).start()

    return (
        dbc.Alert(
            [html.I(className="fas fa-check me-2"), f"Category updated to '{category}'. ML will retrain in background."],
            color="success",
            duration=4000,
        ),
        n_clicks,  # trigger table refresh
    )


# ───────────────────────────────────────────
# Uncategorized review modal
# ───────────────────────────────────────────
@app.callback(
    Output("uncategorized-modal", "is_open"),
    Output("uncategorized-review-body", "children"),
    Input("show-uncategorized-btn", "n_clicks"),
    Input("close-uncat-modal-btn", "n_clicks"),
    State("uncategorized-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_uncategorized_modal(show_clicks, close_clicks, is_open):
    trigger = ctx.triggered_id
    if trigger == "close-uncat-modal-btn":
        return False, no_update

    uncategorized = get_uncategorized_transactions()
    sym = _currency()

    if not uncategorized:
        body = dbc.Alert(
            [html.I(className="fas fa-check-circle me-2"), "All transactions are categorized!"],
            color="success",
        )
        return True, body

    rows = []
    for txn in uncategorized[:50]:
        rows.append(html.Tr([
            html.Td(txn["date"]),
            html.Td(txn["description"], style={"maxWidth": "300px", "overflow": "hidden", "textOverflow": "ellipsis"}),
            html.Td(f"{sym}{txn['amount']:,.2f}"),
            html.Td(txn["transaction_type"]),
        ]))

    body = html.Div([
        dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                f"{len(uncategorized)} transaction(s) need categorization. ",
                "Close this dialog and click on any yellow-highlighted row in the table to assign a category.",
            ],
            color="info",
        ),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Date"), html.Th("Description"), html.Th("Amount"), html.Th("Type"),
            ])),
            html.Tbody(rows),
        ], bordered=True, hover=True, size="sm", striped=True),
        html.Small(f"Showing first {min(50, len(uncategorized))} of {len(uncategorized)}", className="text-muted")
        if len(uncategorized) > 50 else "",
    ])

    return True, body


# ───────────────────────────────────────────
# CSV upload
# ───────────────────────────────────────────
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

        children = [
            html.I(className="fas fa-check-circle me-2"),
            html.Strong("Upload Successful! "),
            f"Processed {result['total_rows']} rows: "
            f"{result['inserted']} inserted, {result['skipped']} skipped (duplicates).",
        ]

        if result["uncategorized"]:
            children.extend([
                html.Br(), html.Br(),
                html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                html.Strong(f"{len(result['uncategorized'])} transactions could not be auto-classified. "),
                "Go to the ",
                html.A("Transactions page", href="/transactions", className="fw-bold"),
                " and click on yellow-highlighted rows to assign categories. ",
                "Each correction trains the ML model so it learns for next time.",
            ])
            return dbc.Alert(children, color="warning")

        return dbc.Alert(children, color="success")

    except ValueError as e:
        return dbc.Alert([html.I(className="fas fa-exclamation-circle me-2"), str(e)], color="danger")
    except Exception as e:
        return dbc.Alert([html.I(className="fas fa-exclamation-circle me-2"), f"Error: {e}"], color="danger")


# ───────────────────────────────────────────
# CSV export
# ───────────────────────────────────────────
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

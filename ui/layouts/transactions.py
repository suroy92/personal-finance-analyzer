from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

from models.keywords import ALL_EXPENSE_CATEGORIES, ALL_SAVINGS_CATEGORIES, ALL_INCOME_CATEGORIES


def layout():
    all_categories = ALL_INCOME_CATEGORIES + ALL_EXPENSE_CATEGORIES + ALL_SAVINGS_CATEGORIES

    return html.Div([
        html.H3("Transactions", className="mb-4"),

        # Filters
        dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText(html.I(className="fas fa-search")),
                    dbc.Input(id="txn-search", placeholder="Search transactions...", type="text"),
                ]),
            ], md=3),
            dbc.Col([
                dbc.Select(
                    id="txn-type-filter",
                    options=[
                        {"label": "All Types", "value": "all"},
                        {"label": "Credit (Income)", "value": "Credit"},
                        {"label": "Debit (Expense)", "value": "Debit"},
                    ],
                    value="all",
                ),
            ], md=2),
            dbc.Col([
                dbc.Select(
                    id="txn-category-filter",
                    options=[{"label": "All Categories", "value": "all"}]
                    + [{"label": c, "value": c} for c in all_categories]
                    + [{"label": "Uncategorized", "value": "_uncategorized"}],
                    value="all",
                ),
            ], md=3),
            dbc.Col([
                dbc.Input(id="txn-month-filter", type="month", value=""),
            ], md=2),
            dbc.Col([
                dbc.Button(
                    [html.I(className="fas fa-exclamation-triangle me-1"), "Review Uncategorized"],
                    id="show-uncategorized-btn",
                    color="warning",
                    size="sm",
                    className="w-100",
                ),
            ], md=2),
        ], className="mb-3"),

        # Transactions table — click a row to edit
        html.P("Click any row to edit its category.", className="text-muted small mb-2"),
        dash_table.DataTable(
            id="transactions-table",
            columns=[
                {"name": "Date", "id": "date"},
                {"name": "Description", "id": "description"},
                {"name": "Amount", "id": "amount", "type": "numeric",
                 "format": dash_table.FormatTemplate.money(2)},
                {"name": "Type", "id": "transaction_type"},
                {"name": "Category", "id": "category"},
            ],
            page_size=20,
            sort_action="native",
            filter_action="native",
            row_selectable="single",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px", "fontSize": "0.9rem"},
            style_header={"fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"filter_query": "{transaction_type} = Credit"},
                 "className": "row-credit"},
                {"if": {"filter_query": "{transaction_type} = Debit"},
                 "className": "row-debit"},
                {"if": {"filter_query": "{category} is nil"},
                 "className": "row-uncategorized"},
            ],
        ),

        html.Div(id="txn-count-info", className="text-muted mt-2"),

        # Edit category modal — appears when a row is clicked
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Edit Transaction Category")),
            dbc.ModalBody([
                html.Div(id="edit-txn-details"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Transaction Type"),
                        dbc.Select(
                            id="edit-txn-type",
                            options=[
                                {"label": "Expense", "value": "Expense"},
                                {"label": "Savings/Investment", "value": "Savings/Investment"},
                                {"label": "Income", "value": "Income"},
                            ],
                        ),
                    ], md=6),
                    dbc.Col([
                        dbc.Label("Category"),
                        dbc.Select(id="edit-txn-category", options=[]),
                    ], md=6),
                ]),
            ]),
            dbc.ModalFooter([
                dbc.Button("Save", id="save-category-btn", color="primary"),
                dbc.Button("Cancel", id="cancel-edit-btn", color="secondary", className="ms-2"),
            ]),
        ], id="edit-category-modal", is_open=False, centered=True),

        # Hidden store for selected transaction hash
        dcc.Store(id="selected-txn-hash"),
        dcc.Store(id="category-save-trigger"),

        html.Div(id="edit-feedback", className="mt-2"),

        # Uncategorized review modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Review Uncategorized Transactions")),
            dbc.ModalBody(id="uncategorized-review-body"),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-uncat-modal-btn", color="secondary"),
            ),
        ], id="uncategorized-modal", is_open=False, size="xl", centered=True),
    ])

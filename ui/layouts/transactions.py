from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc


def layout():
    return html.Div([
        html.H3("Transactions", className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText(html.I(className="fas fa-search")),
                    dbc.Input(id="txn-search", placeholder="Search transactions...", type="text"),
                ]),
            ], md=4),
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
                    options=[{"label": "All Categories", "value": "all"}],
                    value="all",
                ),
            ], md=3),
            dbc.Col([
                dbc.Input(id="txn-month-filter", type="month", value=""),
            ], md=3),
        ], className="mb-3"),

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
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px", "fontSize": "0.9rem"},
            style_header={"backgroundColor": "#2c3e50", "color": "white", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"filter_query": "{transaction_type} = Credit"},
                 "backgroundColor": "#d4edda"},
                {"if": {"filter_query": "{transaction_type} = Debit"},
                 "backgroundColor": "#f8d7da"},
            ],
        ),

        html.Div(id="txn-count-info", className="text-muted mt-2"),
    ])

import plotly.graph_objects as go
import plotly.express as px
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

from ui.app import app
from services.budget_service import set_budget, get_budget_vs_actual, apply_50_30_20_rule, get_all_budgets
from services.suggestion_service import get_spending_ratio_analysis
from services.transaction_service import get_summary
from core.config import get_config


def _currency():
    return get_config().get("currency", {}).get("symbol", "\u20B9")


@app.callback(
    Output("budget-set-feedback", "children"),
    Input("set-budget-btn", "n_clicks"),
    State("budget-category", "value"),
    State("budget-amount", "value"),
    prevent_initial_call=True,
)
def handle_set_budget(n_clicks, category, amount):
    if not category or not amount:
        return dbc.Alert("Please select a category and enter an amount.", color="warning")
    set_budget(category, float(amount))
    sym = _currency()
    return dbc.Alert(f"Budget set: {category} = {sym}{float(amount):,.0f}/month", color="success")


@app.callback(
    Output("budget-vs-actual-chart", "figure"),
    Output("budget-details-table", "children"),
    Input("set-budget-btn", "n_clicks"),
    Input("budget-month-select", "value"),
    Input("url", "pathname"),
)
def update_budget_chart(_, month, pathname):
    if pathname != "/budgets":
        return go.Figure(), ""

    data = get_budget_vs_actual(month if month else None)
    sym = _currency()

    if not data:
        fig = go.Figure().add_annotation(text="No budgets set yet", showarrow=False)
        return fig, html.P("Set budgets above to see comparison.", className="text-muted")

    categories = [d["category"] for d in data]
    budgeted = [d["budget"] for d in data]
    spent = [d["spent"] for d in data]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Budget", x=categories, y=budgeted, marker_color="#007bff"))
    fig.add_trace(go.Bar(name="Actual", x=categories, y=spent, marker_color=[
        "#dc3545" if d["status"] == "over" else "#ffc107" if d["status"] == "warning" else "#28a745"
        for d in data
    ]))
    fig.update_layout(barmode="group", template="plotly_white", margin=dict(t=20, b=60))

    # Details table
    rows = []
    for d in data:
        status_badge = dbc.Badge(
            d["status"].upper(),
            color="danger" if d["status"] == "over" else ("warning" if d["status"] == "warning" else "success"),
        )
        rows.append(html.Tr([
            html.Td(d["category"]),
            html.Td(f"{sym}{d['budget']:,.0f}"),
            html.Td(f"{sym}{d['spent']:,.0f}"),
            html.Td(f"{sym}{d['remaining']:,.0f}"),
            html.Td(f"{d['utilization_pct']}%"),
            html.Td(status_badge),
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Category"), html.Th("Budget"), html.Th("Spent"),
            html.Th("Remaining"), html.Th("Used"), html.Th("Status"),
        ])),
        html.Tbody(rows),
    ], bordered=True, hover=True, size="sm", className="mt-3")

    return fig, table


@app.callback(
    Output("rule-analysis-chart", "figure"),
    Output("rule-analysis-details", "children"),
    Input("url", "pathname"),
)
def update_rule_analysis(pathname):
    if pathname != "/budgets":
        return go.Figure(), ""

    ratio = get_spending_ratio_analysis()
    if "error" in ratio:
        return go.Figure().add_annotation(text=ratio["error"], showarrow=False), ""

    # Actual vs ideal comparison
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Actual",
        x=["Needs", "Wants", "Savings"],
        y=[ratio["needs_pct"], ratio["wants_pct"], ratio["savings_pct"]],
        marker_color=["#17a2b8", "#ffc107", "#28a745"],
    ))
    fig.add_trace(go.Bar(
        name="Ideal (50/30/20)",
        x=["Needs", "Wants", "Savings"],
        y=[50, 30, 20],
        marker_color=["rgba(23,162,184,0.3)", "rgba(255,193,7,0.3)", "rgba(40,167,69,0.3)"],
    ))
    fig.update_layout(barmode="group", template="plotly_white", margin=dict(t=20, b=40),
                      yaxis_title="% of Income")

    sym = _currency()
    details = html.Div([
        html.H5("Your Spending Split", className="mb-3"),
        html.Div([
            html.Div([html.Strong("Needs"), html.Br(),
                      html.Span(f"{ratio['needs_pct']}%", className="h4"),
                      html.Span(f" ({sym}{ratio['needs']:,.0f})", className="text-muted")],
                     className="mb-3"),
            html.Div([html.Strong("Wants"), html.Br(),
                      html.Span(f"{ratio['wants_pct']}%", className="h4"),
                      html.Span(f" ({sym}{ratio['wants']:,.0f})", className="text-muted")],
                     className="mb-3"),
            html.Div([html.Strong("Savings"), html.Br(),
                      html.Span(f"{ratio['savings_pct']}%", className="h4"),
                      html.Span(f" ({sym}{ratio['savings']:,.0f})", className="text-muted")],
                     className="mb-3"),
        ]),
    ])

    return fig, details

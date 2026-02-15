import plotly.graph_objects as go
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

from ui.app import app
from ui.theme_utils import get_colors, themed_layout
from services.suggestion_service import (
    generate_suggestions,
    what_if_calculator,
    get_subscription_audit,
    get_top_discretionary_spending,
    CATEGORY_TIPS,
)
from core.config import get_config


def _currency():
    return get_config().get("currency", {}).get("symbol", "\u20B9")


@app.callback(
    Output("suggestions-body", "children"),
    Input("url", "pathname"),
)
def update_suggestions(pathname):
    if pathname != "/suggestions":
        return []

    suggestions = generate_suggestions()
    if not suggestions:
        return html.P("No suggestions at this time. Upload more data to get personalized recommendations.",
                      className="text-muted")

    items = []
    for s in suggestions:
        icon = "fa-exclamation-triangle" if s["priority"] == "high" else "fa-info-circle"
        color = "danger" if s["priority"] == "high" else "info"
        badge = dbc.Badge(s["type"].replace("_", " ").title(), color="secondary", className="ms-2")
        saving_text = ""
        if "potential_saving" in s:
            sym = _currency()
            saving_text = f" (Potential saving: {sym}{s['potential_saving']:,.0f})"

        items.append(
            dbc.Alert([
                html.I(className=f"fas {icon} me-2"),
                html.Strong(s["category"]),
                badge,
                html.Br(),
                s["message"],
                html.Strong(saving_text) if saving_text else "",
            ], color=color, className="mb-2")
        )

    return html.Div(items)


@app.callback(
    Output("whatif-result", "children"),
    Input("whatif-btn", "n_clicks"),
    State("whatif-category", "value"),
    State("whatif-pct", "value"),
    prevent_initial_call=True,
)
def handle_whatif(n_clicks, category, pct):
    if not category or not pct:
        return dbc.Alert("Select a category and percentage.", color="warning")

    result = what_if_calculator(category, float(pct))
    sym = _currency()

    if "error" in result:
        return dbc.Alert(result["error"], color="warning")

    return html.Div([
        html.H5(f"{sym}{result['annual_saving']:,.0f}/year", className="text-success fw-bold"),
        html.P(f"Monthly saving: {sym}{result['monthly_saving']:,.0f}", className="mb-0 text-muted"),
    ])


@app.callback(
    Output("subscription-audit-body", "children"),
    Input("url", "pathname"),
)
def update_subscription_audit(pathname):
    if pathname != "/suggestions":
        return []

    subs = get_subscription_audit()
    sym = _currency()

    if not subs:
        return html.P("No recurring subscriptions detected.", className="text-muted")

    rows = []
    for s in subs:
        rows.append(html.Tr([
            html.Td(s["description"]),
            html.Td(f"{s['occurrences']}x"),
            html.Td(f"{sym}{s['avg_amount']:,.0f}"),
            html.Td(f"{sym}{s['estimated_annual']:,.0f}"),
        ]))

    total_annual = sum(s["estimated_annual"] for s in subs)

    return html.Div([
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Subscription"), html.Th("Frequency"), html.Th("Avg Amount"),
                html.Th("Est. Annual"),
            ])),
            html.Tbody(rows),
        ], bordered=True, hover=True, size="sm"),
        html.Strong(f"Total estimated annual subscription cost: {sym}{total_annual:,.0f}"),
    ])


@app.callback(
    Output("discretionary-chart", "figure"),
    Input("url", "pathname"),
    Input("theme-store", "data"),
)
def update_discretionary_chart(pathname, theme):
    if pathname != "/suggestions":
        return go.Figure()

    data = get_top_discretionary_spending()
    if not data:
        return go.Figure().add_annotation(text="No discretionary spending data", showarrow=False)

    c = get_colors(theme)
    categories = [d["category"] for d in data]
    totals = [d["total"] for d in data]

    fig = go.Figure(go.Bar(
        x=totals, y=categories, orientation="h",
        marker_color=c["orange"],
        text=[f"{_currency()}{t:,.0f}" for t in totals],
        textposition="auto",
    ))
    fig.update_layout(xaxis_title=f"Total Spent ({_currency()})",
                      yaxis=dict(autorange="reversed"),
                      **themed_layout(theme, margin=dict(t=20, l=120)))
    return fig

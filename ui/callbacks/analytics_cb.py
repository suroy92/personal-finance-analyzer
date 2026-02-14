import plotly.graph_objects as go
import plotly.express as px
from dash import Input, Output, html
import dash_bootstrap_components as dbc
import pandas as pd

from ui.app import app
from services.analytics import (
    get_monthly_trends,
    detect_anomalies,
    get_category_growth_rates,
    get_seasonal_patterns,
)
from services.transaction_service import get_category_breakdown
from core.config import get_config
from core.database import execute_query


def _currency():
    return get_config().get("currency", {}).get("symbol", "\u20B9")


@app.callback(
    Output("moving-avg-chart", "figure"),
    Input("url", "pathname"),
)
def update_moving_avg(pathname):
    if pathname != "/analytics":
        return go.Figure()

    data = get_monthly_trends()
    if not data:
        return go.Figure().add_annotation(text="No data available", showarrow=False)

    df = pd.DataFrame(data)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["month"], y=df["expenses"], name="Expenses", marker_color="rgba(220,53,69,0.5)"))
    fig.add_trace(go.Scatter(x=df["month"], y=df["expense_ma3"], mode="lines", name="3-Month MA",
                             line=dict(color="#fd7e14", width=3)))
    fig.add_trace(go.Scatter(x=df["month"], y=df["expense_ma6"], mode="lines", name="6-Month MA",
                             line=dict(color="#6f42c1", width=3, dash="dash")))
    fig.update_layout(template="plotly_white", margin=dict(t=20, b=40),
                      yaxis_title=f"Amount ({_currency()})",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return fig


@app.callback(
    Output("anomalies-body", "children"),
    Input("url", "pathname"),
)
def update_anomalies(pathname):
    if pathname != "/analytics":
        return []

    anomalies = detect_anomalies()
    sym = _currency()

    if not anomalies:
        return html.P("No spending anomalies detected.", className="text-muted")

    items = []
    for a in anomalies[:10]:
        items.append(
            dbc.ListGroupItem([
                html.Div([
                    html.Strong(f"{a['category']}"),
                    html.Span(f" in {a['month']}", className="text-muted"),
                ]),
                html.Small(
                    f"Spent {sym}{a['amount']:,.0f} vs avg {sym}{a['average']:,.0f} "
                    f"(+{a['spike_pct']}%)",
                    className="text-danger",
                ),
            ])
        )

    return dbc.ListGroup(items)


@app.callback(
    Output("growth-rates-chart", "figure"),
    Input("url", "pathname"),
)
def update_growth_rates(pathname):
    if pathname != "/analytics":
        return go.Figure()

    data = get_category_growth_rates()
    if not data:
        return go.Figure().add_annotation(text="Need more data", showarrow=False)

    df = pd.DataFrame(data[:10])
    colors = ["#dc3545" if g > 0 else "#28a745" for g in df["growth_pct"]]
    fig = go.Figure(go.Bar(x=df["growth_pct"], y=df["category"], orientation="h", marker_color=colors))
    fig.update_layout(template="plotly_white", margin=dict(t=20, l=120),
                      xaxis_title="Growth %", yaxis=dict(autorange="reversed"))
    return fig


@app.callback(
    Output("seasonal-chart", "figure"),
    Input("url", "pathname"),
)
def update_seasonal(pathname):
    if pathname != "/analytics":
        return go.Figure()

    data = get_seasonal_patterns()
    if not data:
        return go.Figure().add_annotation(text="No data", showarrow=False)

    df = pd.DataFrame(data)
    colors = ["#dc3545" if v > 0 else "#28a745" for v in df["vs_average_pct"]]
    fig = go.Figure(go.Bar(
        x=df["month_name"], y=df["vs_average_pct"], marker_color=colors,
        text=[f"{v:+.1f}%" for v in df["vs_average_pct"]], textposition="auto",
    ))
    fig.update_layout(template="plotly_white", margin=dict(t=20, b=40),
                      yaxis_title="vs Average (%)")
    return fig


@app.callback(
    Output("category-time-chart", "figure"),
    Input("url", "pathname"),
)
def update_category_time(pathname):
    if pathname != "/analytics":
        return go.Figure()

    rows = execute_query(
        """SELECT substr(date, 1, 7) as month, category, SUM(amount) as total
           FROM daily_transactions
           WHERE transaction_type = 'Debit' AND category IS NOT NULL
           GROUP BY substr(date, 1, 7), category
           ORDER BY month""",
        fetch=True,
    )
    if not rows:
        return go.Figure().add_annotation(text="No data", showarrow=False)

    df = pd.DataFrame([dict(r) for r in rows])
    fig = px.area(df, x="month", y="total", color="category")
    fig.update_layout(template="plotly_white", margin=dict(t=20, b=40),
                      yaxis_title=f"Amount ({_currency()})")
    return fig

import plotly.graph_objects as go
import plotly.express as px
from dash import Input, Output, html
import dash_bootstrap_components as dbc
import pandas as pd

from ui.app import app
from ui.layouts.dashboard import summary_card
from ui.theme_utils import get_colors, themed_layout
from services.transaction_service import get_summary, get_monthly_breakdown, get_category_breakdown, get_daily_spending
from services.analytics import get_monthly_trends, forecast_next_month
from services.budget_service import get_budget_vs_actual
from core.config import get_config


def _currency():
    return get_config().get("currency", {}).get("symbol", "\u20B9")


@app.callback(
    Output("summary-cards", "children"),
    Input("dashboard-refresh", "n_intervals"),
)
def update_summary_cards(_):
    s = get_summary()
    sym = _currency()
    net = s["total_income"] - s["total_expenses"]

    return [
        dbc.Col(summary_card("Total Income", f"{sym}{s['total_income']:,.0f}", "fa-arrow-down", "summary-card-income"), md=3),
        dbc.Col(summary_card("Total Expenses", f"{sym}{s['total_expenses']:,.0f}", "fa-arrow-up", "summary-card-expense"), md=3),
        dbc.Col(summary_card("Savings & Investments", f"{sym}{s['total_savings']:,.0f}", "fa-piggy-bank", "summary-card-savings"), md=3),
        dbc.Col(summary_card("Net Position", f"{sym}{net:,.0f}", "fa-balance-scale", "summary-card-net"), md=3),
    ]


@app.callback(
    Output("monthly-trend-chart", "figure"),
    Input("dashboard-refresh", "n_intervals"),
    Input("theme-store", "data"),
)
def update_monthly_trend(_, theme):
    data = get_monthly_breakdown()
    if not data:
        return go.Figure().add_annotation(text="No data available", showarrow=False)

    c = get_colors(theme)
    df = pd.DataFrame(data)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["month"], y=df["income"], name="Income", marker_color=c["green"]))
    fig.add_trace(go.Bar(x=df["month"], y=df["expenses"], name="Expenses", marker_color=c["red"]))
    fig.add_trace(go.Bar(x=df["month"], y=df["savings"], name="Savings", marker_color=c["blue"]))
    fig.update_layout(barmode="group", legend=dict(orientation="h", yanchor="bottom", y=1.02),
                      **themed_layout(theme, margin=dict(t=20, b=40)))
    return fig


@app.callback(
    Output("expense-pie-chart", "figure"),
    Input("dashboard-refresh", "n_intervals"),
    Input("theme-store", "data"),
)
def update_expense_pie(_, theme):
    data = get_category_breakdown("Debit")
    if not data:
        return go.Figure().add_annotation(text="No data", showarrow=False)

    df = pd.DataFrame(data)
    fig = px.pie(df, values="total", names="category", hole=0.4)
    fig.update_layout(showlegend=True, **themed_layout(theme, margin=dict(t=20, b=20)))
    return fig


@app.callback(
    Output("savings-rate-chart", "figure"),
    Input("dashboard-refresh", "n_intervals"),
    Input("theme-store", "data"),
)
def update_savings_rate(_, theme):
    data = get_monthly_trends()
    if not data:
        return go.Figure().add_annotation(text="No data", showarrow=False)

    c = get_colors(theme)
    df = pd.DataFrame(data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["savings_rate"], mode="lines+markers",
        name="Savings Rate %", line=dict(color=c["blue"], width=3),
    ))
    fig.add_hline(y=20, line_dash="dash", line_color=c["green"],
                  annotation_text="20% target")
    fig.update_layout(yaxis_title="Savings Rate (%)",
                      **themed_layout(theme, margin=dict(t=20, b=40)))
    return fig


@app.callback(
    Output("spending-heatmap", "figure"),
    Input("dashboard-refresh", "n_intervals"),
    Input("theme-store", "data"),
)
def update_heatmap(_, theme):
    data = get_daily_spending(months_back=6)
    if not data:
        return go.Figure().add_annotation(text="No data", showarrow=False)

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["weekday"] = df["date"].dt.day_name()
    df["week"] = df["date"].dt.isocalendar().week.astype(int)

    pivot = df.pivot_table(values="total", index="weekday", columns="week", aggfunc="sum", fill_value=0)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=[str(w) for w in pivot.columns], y=pivot.index,
        colorscale="RdYlGn_r", hovertemplate="Week %{x}<br>%{y}<br>Spent: %{z:,.0f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Week Number", yaxis_title="",
                      **themed_layout(theme, margin=dict(t=20, b=40)))
    return fig


@app.callback(
    Output("forecast-card-body", "children"),
    Input("dashboard-refresh", "n_intervals"),
)
def update_forecast(_):
    forecast = forecast_next_month()
    sym = _currency()

    if "error" in forecast:
        return html.P(forecast["error"], className="text-muted")

    trend_icon_exp = "fa-arrow-up text-danger" if forecast["expense_trend"] == "increasing" else "fa-arrow-down text-success"
    trend_icon_inc = "fa-arrow-up text-success" if forecast["income_trend"] == "increasing" else "fa-arrow-down text-danger"

    return html.Div([
        html.Div([
            html.P("Projected Expenses", className="text-muted mb-1"),
            html.H5([
                f"{sym}{forecast['forecast_expenses']:,.0f} ",
                html.I(className=f"fas {trend_icon_exp}"),
            ]),
        ], className="mb-3"),
        html.Div([
            html.P("Projected Income", className="text-muted mb-1"),
            html.H5([
                f"{sym}{forecast['forecast_income']:,.0f} ",
                html.I(className=f"fas {trend_icon_inc}"),
            ]),
        ]),
        html.Small(f"Based on {forecast['months_analyzed']} months of data", className="text-muted"),
    ])


@app.callback(
    Output("budget-status-body", "children"),
    Input("dashboard-refresh", "n_intervals"),
)
def update_budget_status(_):
    data = get_budget_vs_actual()
    if not data:
        return html.P("No budgets configured. Go to Budgets page to set them up.", className="text-muted")

    items = []
    for b in data[:5]:
        color = "danger" if b["status"] == "over" else ("warning" if b["status"] == "warning" else "success")
        items.append(
            html.Div([
                html.Div([
                    html.Strong(b["category"]),
                    html.Span(f" {b['utilization_pct']}%", className=f"text-{color} ms-2"),
                ], className="d-flex justify-content-between"),
                dbc.Progress(value=min(b["utilization_pct"], 100), color=color, className="mb-2",
                             style={"height": "8px"}),
            ])
        )

    return html.Div(items)

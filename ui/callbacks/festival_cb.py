import plotly.graph_objects as go
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

from ui.app import app
from ui.theme_utils import get_colors, themed_layout
from services.festival_service import (
    get_upcoming_festivals,
    get_festive_spending_analysis,
    get_all_festivals,
    add_festival,
    remove_festival,
)
from core.config import get_config


def _currency():
    return get_config().get("currency", {}).get("symbol", "\u20B9")


@app.callback(
    Output("upcoming-festivals-body", "children"),
    Input("url", "pathname"),
    Input("add-festival-btn", "n_clicks"),
)
def update_upcoming_festivals(pathname, _):
    if pathname != "/festivals":
        return []

    upcoming = get_upcoming_festivals(days_ahead=60)
    if not upcoming:
        return html.P("No festivals coming up in the next 60 days.", className="text-muted")

    items = []
    for f in upcoming:
        days = f["days_until"]
        if days <= 7:
            urgency_color = "danger"
            urgency_text = f"{days} day{'s' if days != 1 else ''} away!"
        elif days <= 14:
            urgency_color = "warning"
            urgency_text = f"{days} days away"
        else:
            urgency_color = "info"
            urgency_text = f"{days} days away"

        sym = _currency()
        items.append(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H5([
                            f["name"],
                            dbc.Badge(urgency_text, color=urgency_color, className="ms-2"),
                        ]),
                        html.P(f["message"], className="mb-1"),
                        html.Small(f"Date: {f['date']} | Duration: {f['duration_days']} days",
                                   className="text-muted"),
                        html.Br(),
                        html.Small(
                            f"Historical avg spend: {sym}{f['historical_avg_spend']:,.0f} | "
                            f"Suggested extra saving: {sym}{f['suggested_saving']:,.0f}",
                            className="text-muted",
                        ) if f["historical_avg_spend"] > 0 else "",
                    ]),
                ]),
            ], className="mb-2 shadow-sm")
        )

    return html.Div(items)


@app.callback(
    Output("festive-comparison-chart", "figure"),
    Output("festive-stats-body", "children"),
    Input("url", "pathname"),
    Input("theme-store", "data"),
)
def update_festive_comparison(pathname, theme):
    if pathname != "/festivals":
        return go.Figure(), ""

    analysis = get_festive_spending_analysis()
    sym = _currency()

    if not analysis or (isinstance(analysis, dict) and analysis.get("festive_months_count", 0) == 0):
        return go.Figure().add_annotation(text="Not enough data yet", showarrow=False), \
               html.P("Upload more months of data to see festive vs normal spending analysis.", className="text-muted")

    c = get_colors(theme)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Festive Months", "Normal Months"],
        y=[analysis["festive_months_avg"], analysis["normal_months_avg"]],
        marker_color=[c["red"], c["green"]],
        text=[f"{sym}{analysis['festive_months_avg']:,.0f}", f"{sym}{analysis['normal_months_avg']:,.0f}"],
        textposition="auto",
    ))
    fig.update_layout(yaxis_title=f"Average Monthly Spending ({sym})",
                      **themed_layout(theme, margin=dict(t=20, b=40)))

    stats = html.Div([
        html.H5("Festive Season Impact", className="mb-3"),
        html.P([
            "Average festive month spending: ",
            html.Strong(f"{sym}{analysis['festive_months_avg']:,.0f}"),
        ]),
        html.P([
            "Average normal month spending: ",
            html.Strong(f"{sym}{analysis['normal_months_avg']:,.0f}"),
        ]),
        html.P([
            "Extra festive spending: ",
            html.Strong(f"{sym}{analysis['difference']:,.0f}", className="text-danger"),
            f" ({analysis['difference_pct']:+.1f}%)",
        ]),
        html.Hr(),
        html.P([
            "Recommendation: Save an extra ",
            html.Strong(f"{sym}{analysis['difference'] / 12:,.0f}/month"),
            " to cover festive season expenses.",
        ], className="text-info"),
    ])

    return fig, stats


@app.callback(
    Output("add-festival-feedback", "children"),
    Input("add-festival-btn", "n_clicks"),
    State("new-festival-name", "value"),
    State("new-festival-month", "value"),
    State("new-festival-day", "value"),
    State("new-festival-duration", "value"),
    prevent_initial_call=True,
)
def handle_add_festival(n_clicks, name, month, day, duration):
    if not name or not month or not day:
        return dbc.Alert("Please fill in all fields.", color="warning")
    add_festival(name, int(month), int(day), int(duration or 1))
    return dbc.Alert(f"Festival '{name}' added successfully!", color="success")


@app.callback(
    Output("festival-list-body", "children"),
    Input("add-festival-btn", "n_clicks"),
    Input("url", "pathname"),
)
def update_festival_list(_, pathname):
    if pathname != "/festivals":
        return []

    festivals = get_all_festivals()
    if not festivals:
        return html.P("No festivals configured.", className="text-muted")

    month_names = [
        "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    rows = []
    for f in festivals:
        m = f["month"] if f["month"] <= 12 else 1
        rows.append(html.Tr([
            html.Td(f["name"]),
            html.Td(f"{f['day']} {month_names[m]}"),
            html.Td(f"{f['duration_days']} day(s)"),
        ]))

    return dbc.Table([
        html.Thead(html.Tr([html.Th("Festival"), html.Th("Date"), html.Th("Duration")])),
        html.Tbody(rows),
    ], bordered=True, hover=True, size="sm")

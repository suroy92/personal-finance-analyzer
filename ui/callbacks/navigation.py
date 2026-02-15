from dash import Input, Output, html
import dash_bootstrap_components as dbc

from ui.app import app
from ui.layouts import (
    dashboard,
    transactions,
    analytics,
    budgets,
    suggestions,
    festivals,
    import_data,
    settings,
)
from services.festival_service import get_upcoming_festivals


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/" or pathname == "":
        return dashboard.layout()
    elif pathname == "/transactions":
        return transactions.layout()
    elif pathname == "/analytics":
        return analytics.layout()
    elif pathname == "/budgets":
        return budgets.layout()
    elif pathname == "/suggestions":
        return suggestions.layout()
    elif pathname == "/festivals":
        return festivals.layout()
    elif pathname == "/import":
        return import_data.layout()
    elif pathname == "/settings":
        return settings.layout()
    return html.Div([
        html.H3("404 - Page Not Found"),
        html.P(f"The path '{pathname}' was not found."),
    ])


@app.callback(
    Output("festival-alert-banner", "children"),
    Input("festival-check-interval", "n_intervals"),
)
def update_festival_banner(_):
    upcoming = get_upcoming_festivals()
    if not upcoming:
        return []

    alerts = []
    for f in upcoming[:3]:
        color = "danger" if f["days_until"] <= 7 else "warning"
        alerts.append(
            dbc.Alert(
                [
                    html.I(className="fas fa-bell me-2"),
                    html.Strong(f["name"]),
                    f" — {f['message']}",
                ],
                color=color,
                dismissable=True,
                className="mb-2",
            )
        )

    return alerts

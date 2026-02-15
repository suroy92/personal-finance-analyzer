import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from core.config import get_config

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="Personal Finance Analyzer",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#2c3e50",
    "color": "white",
    "overflowY": "auto",
}

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H4("Finance Analyzer", className="text-white mb-4"),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.2)"}),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-tachometer-alt me-2"), "Dashboard"],
                    href="/",
                    active="exact",
                    className="text-white",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-exchange-alt me-2"), "Transactions"],
                    href="/transactions",
                    active="exact",
                    className="text-white",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-chart-line me-2"), "Analytics"],
                    href="/analytics",
                    active="exact",
                    className="text-white",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-wallet me-2"), "Budgets"],
                    href="/budgets",
                    active="exact",
                    className="text-white",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-lightbulb me-2"), "Suggestions"],
                    href="/suggestions",
                    active="exact",
                    className="text-white",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-bell me-2"), "Festival Alerts"],
                    href="/festivals",
                    active="exact",
                    className="text-white",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-upload me-2"), "Import Data"],
                    href="/import",
                    active="exact",
                    className="text-white",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-cog me-2"), "Settings"],
                    href="/settings",
                    active="exact",
                    className="text-white",
                ),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

# Alert banner for festival notifications
alert_banner = html.Div(id="festival-alert-banner", style=CONTENT_STYLE)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Interval(id="festival-check-interval", interval=3600 * 1000, n_intervals=0),  # hourly
    sidebar,
    alert_banner,
    content,
])

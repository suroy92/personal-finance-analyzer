import dash
from dash import html, dcc, ClientsideFunction, Input, Output, State
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="Personal Finance Analyzer",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

sidebar = html.Div(
    [
        html.H4("Finance Analyzer", className="mb-3"),
        html.Hr(),

        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-tachometer-alt me-2"), "Dashboard"],
                    href="/", active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-exchange-alt me-2"), "Transactions"],
                    href="/transactions", active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-chart-line me-2"), "Analytics"],
                    href="/analytics", active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-wallet me-2"), "Budgets"],
                    href="/budgets", active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-lightbulb me-2"), "Suggestions"],
                    href="/suggestions", active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-bell me-2"), "Festival Alerts"],
                    href="/festivals", active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-upload me-2"), "Import Data"],
                    href="/import", active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-cog me-2"), "Settings"],
                    href="/settings", active="exact",
                ),
            ],
            vertical=True,
            pills=True,
        ),

        # Theme toggle at bottom of sidebar
        html.Div([
            html.Hr(),
            html.Button(
                "Dark Mode",
                id="theme-toggle-btn",
            ),
        ], style={"position": "absolute", "bottom": "1rem", "left": "1rem", "right": "1rem"}),
    ],
    id="pfa-sidebar",
)

content = html.Div(id="page-content")
alert_banner = html.Div(id="festival-alert-banner")

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="theme-store", data="light", storage_type="local"),
    dcc.Interval(id="festival-check-interval", interval=3600 * 1000, n_intervals=0),
    sidebar,
    alert_banner,
    content,
])

# ── Clientside callbacks for theme toggling ──

# Restore theme from localStorage on page load
app.clientside_callback(
    ClientsideFunction(namespace="theme", function_name="initTheme"),
    Output("theme-store", "data"),
    Input("url", "pathname"),
)

# Toggle theme on button click (reads current theme via State, not Input)
app.clientside_callback(
    ClientsideFunction(namespace="theme", function_name="toggle"),
    Output("theme-store", "data", allow_duplicate=True),
    Input("theme-toggle-btn", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)

# Update button label when theme changes
app.clientside_callback(
    ClientsideFunction(namespace="theme", function_name="updateButtonLabel"),
    Output("theme-toggle-btn", "children"),
    Input("theme-store", "data"),
)

"""Theme-aware chart layout helpers for Plotly figures."""


# Color palettes matching theme.css
LIGHT_COLORS = {
    "green": "#1A7F37",
    "red": "#CF222E",
    "blue": "#0969DA",
    "purple": "#8250DF",
    "yellow": "#9A6700",
    "orange": "#BC4C00",
    "cyan": "#0550AE",
    "green_subtle": "rgba(26,127,55,0.5)",
    "red_subtle": "rgba(207,34,46,0.5)",
    "blue_subtle": "rgba(9,105,218,0.3)",
    "yellow_subtle": "rgba(154,103,0,0.3)",
    "cyan_subtle": "rgba(5,80,174,0.3)",
    "green_bar": "rgba(26,127,55,0.3)",
    "text": "#24292F",
    "grid": "#E1E4E8",
}

DARK_COLORS = {
    "green": "#7EE787",
    "red": "#FF7B72",
    "blue": "#79C0FF",
    "purple": "#D2A8FF",
    "yellow": "#D29922",
    "orange": "#E3B341",
    "cyan": "#A5D6FF",
    "green_subtle": "rgba(126,231,135,0.5)",
    "red_subtle": "rgba(255,123,114,0.5)",
    "blue_subtle": "rgba(121,192,255,0.3)",
    "yellow_subtle": "rgba(210,153,34,0.3)",
    "cyan_subtle": "rgba(5,80,174,0.3)",
    "green_bar": "rgba(126,231,135,0.3)",
    "text": "#C9D1D9",
    "grid": "#21262D",
}


def get_colors(theme):
    """Return the color palette for the given theme."""
    return DARK_COLORS if theme == "dark" else LIGHT_COLORS


def themed_layout(theme, **extra):
    """Return a dict of common Plotly layout properties for the current theme."""
    is_dark = theme == "dark"
    colors = DARK_COLORS if is_dark else LIGHT_COLORS
    base = {
        "template": "plotly_dark" if is_dark else "plotly_white",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": colors["text"]},
        "xaxis": {"gridcolor": colors["grid"], "zerolinecolor": colors["grid"]},
        "yaxis": {"gridcolor": colors["grid"], "zerolinecolor": colors["grid"]},
    }
    base.update(extra)
    return base

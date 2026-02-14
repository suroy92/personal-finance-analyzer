import shutil
from dash import Input, Output, html
import dash_bootstrap_components as dbc

from ui.app import app
from models.ml_models import train_models
from core.config import get_config


@app.callback(
    Output("retrain-feedback", "children"),
    Input("retrain-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_retrain(n_clicks):
    try:
        train_models()
        return dbc.Alert("Models retrained successfully!", color="success")
    except Exception as e:
        return dbc.Alert(f"Retrain failed: {e}", color="danger")


@app.callback(
    Output("download-backup", "data"),
    Input("backup-db-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_backup(n_clicks):
    import os
    from datetime import datetime

    cfg = get_config()
    db_path = cfg.get("database", {}).get("path", "personal_finance_analyzer.db")

    if not os.path.exists(db_path):
        return None

    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join("backups", backup_name)
    os.makedirs("backups", exist_ok=True)
    shutil.copy2(db_path, backup_path)

    return dict(content=open(backup_path, "rb").read(), filename=backup_name, type="application/octet-stream")

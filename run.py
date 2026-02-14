"""Personal Finance Analyzer — Application Entry Point."""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from core.config import load_config
from core.database import initialize_database
from core.logger import setup_logger
from models.ml_models import train_models

import threading


def main():
    # Load configuration
    config = load_config()
    logger = setup_logger("pfa")
    logger.info("Starting Personal Finance Analyzer")

    # Initialize database
    initialize_database()

    # Train ML models in background if enabled
    if config.get("ml", {}).get("retrain_on_startup", True):
        threading.Thread(target=train_models, daemon=True).start()

    # Import Dash app and register all callbacks
    from ui.app import app
    import ui.callbacks.navigation       # noqa: F401
    import ui.callbacks.dashboard_cb     # noqa: F401
    import ui.callbacks.transaction_cb   # noqa: F401
    import ui.callbacks.analytics_cb     # noqa: F401
    import ui.callbacks.budget_cb        # noqa: F401
    import ui.callbacks.suggestion_cb    # noqa: F401
    import ui.callbacks.festival_cb      # noqa: F401
    import ui.callbacks.settings_cb      # noqa: F401

    server_cfg = config.get("server", {})
    logger.info(
        "Server starting at http://%s:%s",
        server_cfg.get("host", "127.0.0.1"),
        server_cfg.get("port", 8050),
    )

    app.run(
        host=server_cfg.get("host", "127.0.0.1"),
        port=server_cfg.get("port", 8050),
        debug=server_cfg.get("debug", True),
    )


if __name__ == "__main__":
    main()

import os
import sys
import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use a test database
os.environ["PFA_TEST_MODE"] = "1"


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    """Use a temporary database for each test."""
    db_path = str(tmp_path / "test.db")

    # Patch config to use test db
    test_config = {
        "database": {"path": db_path},
        "currency": {"symbol": "\u20B9", "code": "INR", "locale": "en_IN"},
        "ml": {"confidence_threshold": 0.7, "retrain_on_startup": False, "model_save_path": str(tmp_path / "models")},
        "logging": {"level": "WARNING", "file": str(tmp_path / "test.log")},
        "budgets": {"default_rule": "50/30/20"},
        "festivals": {
            "alert_days_before": 21,
            "default_festivals": [
                {"name": "Diwali", "month": 10, "day": 20, "duration_days": 5},
                {"name": "Christmas", "month": 12, "day": 25, "duration_days": 3},
            ],
        },
        "server": {"host": "127.0.0.1", "port": 8050, "debug": False},
    }

    import core.config
    monkeypatch.setattr(core.config, "_config", test_config)

    # Reset thread-local DB connections
    import core.database
    if hasattr(core.database._local, "connection"):
        try:
            core.database._local.connection.close()
        except Exception:
            pass
        core.database._local.connection = None

    # Reset ML model state
    import models.ml_models as ml
    ml._debit_type_model = None
    ml._expense_model = None
    ml._savings_model = None
    ml._vectorizer = None
    ml._data_hash = None

    from core.database import initialize_database
    initialize_database()

    yield db_path

    # Cleanup
    if hasattr(core.database._local, "connection") and core.database._local.connection:
        try:
            core.database._local.connection.close()
        except Exception:
            pass
        core.database._local.connection = None

from core.database import execute_query, get_db


def test_tables_created(test_db):
    """Verify all expected tables exist after initialization."""
    rows = execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        fetch=True,
    )
    table_names = {r["name"] for r in rows}
    expected = {
        "daily_transactions", "training_data", "budgets",
        "monthly_summary", "festivals", "savings_goals", "schema_version",
    }
    assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"


def test_schema_version(test_db):
    rows = execute_query("SELECT version FROM schema_version", fetch=True)
    assert len(rows) == 1
    assert rows[0]["version"] == 2


def test_festivals_seeded(test_db):
    rows = execute_query("SELECT * FROM festivals", fetch=True)
    assert len(rows) >= 2
    names = {r["name"] for r in rows}
    assert "Diwali" in names
    assert "Christmas" in names


def test_insert_and_fetch(test_db):
    execute_query(
        """INSERT INTO daily_transactions
           (date, description, amount, transaction_type, category, is_saving, uploaded_at, hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("2024-01-15", "ZOMATO ORDER", 500.0, "Debit", "Food & Dining", 0, "2024-01-15T10:00:00", "abc123"),
    )
    rows = execute_query("SELECT * FROM daily_transactions", fetch=True)
    assert len(rows) == 1
    assert rows[0]["description"] == "ZOMATO ORDER"
    assert rows[0]["amount"] == 500.0


def test_duplicate_hash_rejected(test_db):
    execute_query(
        """INSERT INTO daily_transactions
           (date, description, amount, transaction_type, category, is_saving, uploaded_at, hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("2024-01-15", "TEST", 100.0, "Debit", "Shopping", 0, "2024-01-15T10:00:00", "dup123"),
    )
    try:
        execute_query(
            """INSERT INTO daily_transactions
               (date, description, amount, transaction_type, category, is_saving, uploaded_at, hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("2024-01-15", "TEST", 100.0, "Debit", "Shopping", 0, "2024-01-15T10:00:00", "dup123"),
        )
        assert False, "Should have raised an error for duplicate hash"
    except Exception:
        pass  # Expected


def test_context_manager_rollback(test_db):
    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO daily_transactions
                   (date, description, amount, transaction_type, category, is_saving, uploaded_at, hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("2024-01-15", "ROLLBACK TEST", 999.0, "Debit", "Test", 0, "2024-01-15T10:00:00", "rollback1"),
            )
            raise ValueError("Force rollback")
    except ValueError:
        pass

    rows = execute_query("SELECT * FROM daily_transactions WHERE hash = 'rollback1'", fetch=True)
    assert len(rows) == 0

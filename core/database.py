import sqlite3
import threading
import os
from contextlib import contextmanager
from core.config import get_config
from core.logger import setup_logger

logger = setup_logger("pfa.database")

_local = threading.local()

SCHEMA_VERSION = 2


def _db_path():
    cfg = get_config()
    return cfg.get("database", {}).get("path", "personal_finance_analyzer.db")


def get_connection():
    if not hasattr(_local, "connection") or _local.connection is None:
        path = _db_path()
        _local.connection = sqlite3.connect(path)
        _local.connection.row_factory = sqlite3.Row
        _local.connection.execute("PRAGMA journal_mode=WAL")
        _local.connection.execute("PRAGMA foreign_keys=ON")
    return _local.connection


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def execute_query(query, params=(), fetch=False):
    with get_db() as conn:
        cursor = conn.execute(query, params)
        if fetch:
            return cursor.fetchall()
        return None


def initialize_database():
    with get_db() as conn:
        cursor = conn.cursor()

        # Schema version tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)

        # Daily transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                category TEXT,
                is_saving INTEGER DEFAULT 0,
                uploaded_at TEXT NOT NULL,
                hash TEXT UNIQUE
            )
        """)

        # Training data for ML
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                category TEXT NOT NULL
            )
        """)

        # Monthly budgets per category
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(category)
            )
        """)

        # Monthly summaries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL UNIQUE,
                total_income REAL NOT NULL DEFAULT 0,
                total_expenses REAL NOT NULL DEFAULT 0,
                total_savings REAL NOT NULL DEFAULT 0
            )
        """)

        # Festival alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS festivals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                duration_days INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Savings goals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL DEFAULT 0,
                deadline TEXT,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Update schema version
        cursor.execute("DELETE FROM schema_version")
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))

    _seed_festivals()
    logger.info("Database initialized (schema v%d)", SCHEMA_VERSION)


def _seed_festivals():
    cfg = get_config()
    festivals = cfg.get("festivals", {}).get("default_festivals", [])
    with get_db() as conn:
        for f in festivals:
            conn.execute(
                """INSERT OR IGNORE INTO festivals (name, month, day, duration_days)
                   VALUES (?, ?, ?, ?)""",
                (f["name"], f["month"], f["day"], f.get("duration_days", 1)),
            )

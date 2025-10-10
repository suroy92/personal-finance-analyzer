import sqlite3

DB_FILE = 'personal_finance_analyzer.db'

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Daily transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_transactions (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            category TEXT,
            is_saving INTEGER DEFAULT 0,
            uploaded_at TEXT NOT NULL
        )
    """)

    # Training data table for ML
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_data (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def execute_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        results = cursor.fetchall()
    else:
        results = None
    conn.commit()
    conn.close()
    return results

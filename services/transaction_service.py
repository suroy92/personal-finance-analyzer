import re
import hashlib
from datetime import datetime
from typing import Optional, Tuple, List, Dict

import pandas as pd

from core.database import execute_query, get_db
from core.logger import setup_logger
from models.keywords import (
    INCOME_KEYWORDS,
    EXPENSE_KEYWORDS,
    SAVINGS_KEYWORDS,
)
from models.ml_models import (
    predict_debit_type,
    predict_expense_category,
    predict_savings_category,
    train_models,
)
from core.config import get_config

logger = setup_logger("pfa.transactions")


def preprocess_description(desc: str) -> str:
    desc = (desc or "").upper()
    desc = re.sub(r"-\d{6,}", "", desc)
    return " ".join(desc.split())


def _compute_hash(date, description, amount, txn_type):
    raw = f"{date}|{description}|{amount}|{txn_type}"
    return hashlib.sha256(raw.encode()).hexdigest()


def label_with_keywords(description: str) -> Tuple[Optional[str], Optional[str]]:
    for cat, keywords in EXPENSE_KEYWORDS.items():
        if any(k in description for k in keywords):
            return "Expense", cat
    for cat, keywords in SAVINGS_KEYWORDS.items():
        if any(k in description for k in keywords):
            return "Savings/Investment", cat
    for cat, keywords in INCOME_KEYWORDS.items():
        if any(k in description for k in keywords):
            return "Income", cat
    return None, None


def _parse_date(date_str: str) -> str:
    """Try to parse various date formats to ISO YYYY-MM-DD."""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return str(date_str).strip()


def classify_transaction(description: str, amount: float, is_credit: bool):
    """
    Classify a single transaction.
    Returns (transaction_type, category, is_saving).
    """
    cfg = get_config()
    threshold = cfg.get("ml", {}).get("confidence_threshold", 0.7)
    processed = preprocess_description(description)

    if is_credit:
        _, category = label_with_keywords(processed)
        return "Credit", category, 0

    # Debit — determine type
    debit_type, category = label_with_keywords(processed)

    if not debit_type:
        ml_type, ml_conf = predict_debit_type(processed)
        if ml_type and ml_conf > threshold:
            debit_type = ml_type
        else:
            debit_type = "Expense"

    is_saving = 0
    if debit_type and debit_type.lower().startswith("savings"):
        is_saving = 1
        if not category:
            pred, conf = predict_savings_category(processed)
            if pred and conf > threshold:
                category = pred
    else:
        if not category:
            pred, conf = predict_expense_category(processed)
            if pred and conf > threshold:
                category = pred

    return "Debit", category, is_saving


def ingest_csv(file_content: bytes, filename: str) -> Dict:
    """
    Parse and ingest a bank statement CSV.
    Returns summary dict with counts.
    """
    import io
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = df.columns.str.strip()

    required = ["Date", "Narration", "Debit Amount", "Credit Amount"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    df["Debit Amount"] = pd.to_numeric(df["Debit Amount"], errors="coerce").fillna(0.0)
    df["Credit Amount"] = pd.to_numeric(df["Credit Amount"], errors="coerce").fillna(0.0)

    inserted = 0
    skipped = 0
    uncategorized = []

    for _, row in df.iterrows():
        description_raw = str(row["Narration"])
        processed = preprocess_description(description_raw)
        date = _parse_date(row["Date"])

        if row["Credit Amount"] > 0:
            amount = float(row["Credit Amount"])
            is_credit = True
        elif row["Debit Amount"] > 0:
            amount = float(row["Debit Amount"])
            is_credit = False
        else:
            continue

        txn_type, category, is_saving = classify_transaction(description_raw, amount, is_credit)
        txn_hash = _compute_hash(date, processed, amount, txn_type)

        # Check duplicate
        existing = execute_query(
            "SELECT id FROM daily_transactions WHERE hash = ?",
            (txn_hash,),
            fetch=True,
        )
        if existing:
            skipped += 1
            continue

        execute_query(
            """INSERT INTO daily_transactions
               (date, description, amount, transaction_type, category, is_saving, uploaded_at, hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, description_raw, amount, txn_type, category, is_saving,
             datetime.now().isoformat(), txn_hash),
        )

        if category:
            execute_query(
                "INSERT INTO training_data (description, category) VALUES (?, ?)",
                (processed, category),
            )

        if not category:
            uncategorized.append({
                "description": description_raw,
                "amount": amount,
                "type": txn_type,
                "hash": txn_hash,
            })

        inserted += 1

    # Background retrain
    if inserted > 0:
        import threading
        threading.Thread(target=train_models, daemon=True).start()

    logger.info("CSV ingested: %d inserted, %d skipped (duplicate)", inserted, skipped)
    return {
        "inserted": inserted,
        "skipped": skipped,
        "uncategorized": uncategorized,
        "total_rows": len(df),
    }


def update_transaction_category(txn_hash: str, category: str, is_saving: int = 0):
    """Update category for a transaction and add training data."""
    execute_query(
        "UPDATE daily_transactions SET category = ?, is_saving = ? WHERE hash = ?",
        (category, is_saving, txn_hash),
    )
    rows = execute_query(
        "SELECT description FROM daily_transactions WHERE hash = ?",
        (txn_hash,),
        fetch=True,
    )
    if rows:
        processed = preprocess_description(rows[0]["description"])
        execute_query(
            "INSERT INTO training_data (description, category) VALUES (?, ?)",
            (processed, category),
        )
    logger.info("Transaction %s categorized as %s", txn_hash[:8], category)


def get_all_transactions(limit=500, offset=0):
    rows = execute_query(
        """SELECT id, date, description, amount, transaction_type, category, is_saving, uploaded_at
           FROM daily_transactions ORDER BY date DESC LIMIT ? OFFSET ?""",
        (limit, offset),
        fetch=True,
    )
    return [dict(r) for r in rows] if rows else []


def get_transactions_by_month(month: str):
    """month in format YYYY-MM"""
    rows = execute_query(
        """SELECT * FROM daily_transactions WHERE date LIKE ? ORDER BY date""",
        (f"{month}%",),
        fetch=True,
    )
    return [dict(r) for r in rows] if rows else []


def get_summary():
    """Get overall totals."""
    rows = execute_query(
        """SELECT
             SUM(CASE WHEN transaction_type='Credit' THEN amount ELSE 0 END) as total_income,
             SUM(CASE WHEN transaction_type='Debit' THEN amount ELSE 0 END) as total_expenses,
             SUM(CASE WHEN is_saving=1 THEN amount ELSE 0 END) as total_savings,
             COUNT(*) as total_count
           FROM daily_transactions""",
        fetch=True,
    )
    if rows and rows[0]["total_count"]:
        r = rows[0]
        return {
            "total_income": r["total_income"] or 0,
            "total_expenses": r["total_expenses"] or 0,
            "total_savings": r["total_savings"] or 0,
            "total_count": r["total_count"] or 0,
        }
    return {"total_income": 0, "total_expenses": 0, "total_savings": 0, "total_count": 0}


def get_monthly_breakdown():
    """Get income/expense/savings broken down by month."""
    rows = execute_query(
        """SELECT
             substr(date, 1, 7) as month,
             SUM(CASE WHEN transaction_type='Credit' THEN amount ELSE 0 END) as income,
             SUM(CASE WHEN transaction_type='Debit' AND is_saving=0 THEN amount ELSE 0 END) as expenses,
             SUM(CASE WHEN is_saving=1 THEN amount ELSE 0 END) as savings
           FROM daily_transactions
           GROUP BY substr(date, 1, 7)
           ORDER BY month""",
        fetch=True,
    )
    return [dict(r) for r in rows] if rows else []


def get_category_breakdown(transaction_type=None):
    """Get spending by category, optionally filtered by type."""
    if transaction_type:
        rows = execute_query(
            """SELECT category, SUM(amount) as total
               FROM daily_transactions WHERE transaction_type = ?
               GROUP BY category ORDER BY total DESC""",
            (transaction_type,),
            fetch=True,
        )
    else:
        rows = execute_query(
            """SELECT category, SUM(amount) as total
               FROM daily_transactions
               GROUP BY category ORDER BY total DESC""",
            fetch=True,
        )
    return [dict(r) for r in rows] if rows else []


def get_daily_spending(months_back=3):
    """Get daily total spending for recent months."""
    rows = execute_query(
        """SELECT date, SUM(amount) as total
           FROM daily_transactions
           WHERE transaction_type = 'Debit'
           GROUP BY date
           ORDER BY date DESC
           LIMIT ?""",
        (months_back * 31,),
        fetch=True,
    )
    return [dict(r) for r in rows] if rows else []

from datetime import datetime
from typing import List, Dict, Optional

from core.database import execute_query
from core.logger import setup_logger

logger = setup_logger("pfa.budget")


def set_budget(category: str, monthly_limit: float):
    now = datetime.now().isoformat()
    existing = execute_query(
        "SELECT id FROM budgets WHERE category = ?", (category,), fetch=True
    )
    if existing:
        execute_query(
            "UPDATE budgets SET monthly_limit = ?, updated_at = ? WHERE category = ?",
            (monthly_limit, now, category),
        )
    else:
        execute_query(
            "INSERT INTO budgets (category, monthly_limit, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (category, monthly_limit, now, now),
        )
    logger.info("Budget set: %s = %.2f", category, monthly_limit)


def get_all_budgets() -> List[Dict]:
    rows = execute_query("SELECT * FROM budgets ORDER BY category", fetch=True)
    return [dict(r) for r in rows] if rows else []


def delete_budget(category: str):
    execute_query("DELETE FROM budgets WHERE category = ?", (category,))


def get_budget_vs_actual(month: Optional[str] = None) -> List[Dict]:
    """
    Compare budget limits vs actual spending per category for a month.
    month format: YYYY-MM. Defaults to current month.
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")

    budgets = execute_query("SELECT category, monthly_limit FROM budgets", fetch=True)
    if not budgets:
        return []

    results = []
    for b in budgets:
        actual_rows = execute_query(
            """SELECT SUM(amount) as spent FROM daily_transactions
               WHERE category = ? AND transaction_type = 'Debit'
               AND date LIKE ?""",
            (b["category"], f"{month}%"),
            fetch=True,
        )
        spent = actual_rows[0]["spent"] if actual_rows and actual_rows[0]["spent"] else 0

        limit = b["monthly_limit"]
        results.append({
            "category": b["category"],
            "budget": limit,
            "spent": round(spent, 2),
            "remaining": round(limit - spent, 2),
            "utilization_pct": round((spent / limit * 100) if limit > 0 else 0, 1),
            "status": "over" if spent > limit else ("warning" if spent > limit * 0.8 else "ok"),
        })

    results.sort(key=lambda x: x["utilization_pct"], reverse=True)
    return results


def apply_50_30_20_rule(monthly_income: float) -> Dict:
    """Suggest budget allocation based on 50/30/20 rule."""
    return {
        "needs": round(monthly_income * 0.5, 2),
        "wants": round(monthly_income * 0.3, 2),
        "savings": round(monthly_income * 0.2, 2),
        "description": {
            "needs": "Essentials: Rent, Groceries, Utilities, Transportation, Healthcare",
            "wants": "Discretionary: Dining, Shopping, Entertainment, Subscriptions",
            "savings": "Savings & Investments: SIP, FD, Insurance, Emergency Fund",
        },
    }

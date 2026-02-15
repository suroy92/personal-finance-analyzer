from typing import List, Dict
from datetime import datetime

from core.database import execute_query
from core.logger import setup_logger
from services.budget_service import get_budget_vs_actual

logger = setup_logger("pfa.suggestions")

DISCRETIONARY_CATEGORIES = [
    "Food & Dining", "Shopping", "Subscriptions", "Entertainment",
    "Personal Care", "Travel",
]

NEEDS_CATEGORIES = [
    "Rent", "Groceries", "Utilities", "Transportation", "Healthcare",
    "Education", "Fuel",
]

CATEGORY_TIPS = {
    "Food & Dining": [
        "Consider meal prepping on weekends to reduce takeout spending.",
        "Use food delivery coupons and loyalty programs.",
        "Set a weekly dining-out budget and track it.",
    ],
    "Shopping": [
        "Use a 48-hour rule: wait before making non-essential purchases.",
        "Unsubscribe from marketing emails to reduce impulse buying.",
        "Compare prices across platforms before purchasing.",
    ],
    "Subscriptions": [
        "Audit all active subscriptions — cancel unused ones.",
        "Share family plans with household members.",
        "Look for annual plans which are usually cheaper than monthly.",
    ],
    "Transportation": [
        "Consider carpooling or public transport for regular commutes.",
        "Use ride-sharing during off-peak hours for lower fares.",
        "Batch errands to reduce the number of trips.",
    ],
    "Groceries": [
        "Plan weekly meals and make a shopping list before buying.",
        "Buy in bulk for non-perishable items.",
        "Use cashback apps and loyalty cards.",
    ],
    "Fuel": [
        "Maintain proper tire pressure to improve fuel efficiency.",
        "Consider carpooling for daily commutes.",
        "Use fuel reward programs.",
    ],
    "Entertainment": [
        "Look for free events and activities in your city.",
        "Use matinee show timings for cheaper movie tickets.",
        "Set a monthly entertainment budget.",
    ],
    "Utilities": [
        "Switch to LED lighting to reduce electricity bills.",
        "Use energy-efficient appliances.",
        "Turn off standby devices and unplug chargers.",
    ],
}


def get_top_discretionary_spending(months: int = 3) -> List[Dict]:
    """Identify top discretionary spending categories."""
    placeholders = ",".join(["?"] * len(DISCRETIONARY_CATEGORIES))
    rows = execute_query(
        f"""SELECT category, SUM(amount) as total, COUNT(*) as txn_count,
               AVG(amount) as avg_amount
           FROM daily_transactions
           WHERE transaction_type = 'Debit'
             AND category IN ({placeholders})
           GROUP BY category
           ORDER BY total DESC""",
        tuple(DISCRETIONARY_CATEGORIES),
        fetch=True,
    )
    return [dict(r) for r in rows] if rows else []


def get_subscription_audit() -> List[Dict]:
    """Identify recurring subscription-like transactions."""
    rows = execute_query(
        """SELECT description, COUNT(*) as occurrences,
               SUM(amount) as total_spent, AVG(amount) as avg_amount,
               MIN(date) as first_seen, MAX(date) as last_seen
           FROM daily_transactions
           WHERE transaction_type = 'Debit'
             AND (category = 'Subscriptions'
                  OR description LIKE '%SUBSCRIPTION%'
                  OR description LIKE '%RECURRING%')
           GROUP BY description
           HAVING COUNT(*) >= 2
           ORDER BY total_spent DESC""",
        fetch=True,
    )
    results = []
    for r in rows:
        d = dict(r)
        d["estimated_annual"] = round(d["avg_amount"] * 12, 2)
        results.append(d)
    return results


def what_if_calculator(category: str, reduction_pct: float) -> Dict:
    """Calculate savings if spending in a category is reduced by X%."""
    rows = execute_query(
        """SELECT SUM(amount) as total, COUNT(*) as months
           FROM (
               SELECT substr(date, 1, 7) as month, SUM(amount) as amount
               FROM daily_transactions
               WHERE transaction_type = 'Debit' AND category = ?
               GROUP BY substr(date, 1, 7)
           )""",
        (category,),
        fetch=True,
    )
    if not rows or not rows[0]["total"]:
        return {"error": f"No spending data found for {category}"}

    total = rows[0]["total"]
    months = rows[0]["months"]
    monthly_avg = total / months if months > 0 else 0
    monthly_saving = monthly_avg * (reduction_pct / 100)

    return {
        "category": category,
        "current_monthly_avg": round(monthly_avg, 2),
        "reduction_pct": reduction_pct,
        "monthly_saving": round(monthly_saving, 2),
        "annual_saving": round(monthly_saving * 12, 2),
        "new_monthly_avg": round(monthly_avg - monthly_saving, 2),
    }


def get_spending_ratio_analysis() -> Dict:
    """Compare actual spending split against 50/30/20 rule."""
    rows = execute_query(
        """SELECT
             SUM(CASE WHEN transaction_type='Credit' THEN amount ELSE 0 END) as income,
             SUM(CASE WHEN transaction_type='Debit' AND is_saving=0 THEN amount ELSE 0 END) as expenses,
             SUM(CASE WHEN is_saving=1 THEN amount ELSE 0 END) as savings
           FROM daily_transactions""",
        fetch=True,
    )
    if not rows or not rows[0]["income"]:
        return {"error": "No transaction data available"}

    income = rows[0]["income"]
    expenses = rows[0]["expenses"]
    savings = rows[0]["savings"]

    # Classify expenses into needs vs wants
    needs_cats = ",".join(["?"] * len(NEEDS_CATEGORIES))
    needs_rows = execute_query(
        f"""SELECT SUM(amount) as total FROM daily_transactions
           WHERE transaction_type='Debit' AND is_saving=0
           AND category IN ({needs_cats})""",
        tuple(NEEDS_CATEGORIES),
        fetch=True,
    )
    needs = needs_rows[0]["total"] if needs_rows and needs_rows[0]["total"] else 0
    wants = expenses - needs

    return {
        "income": round(income, 2),
        "needs": round(needs, 2),
        "wants": round(wants, 2),
        "savings": round(savings, 2),
        "needs_pct": round(needs / income * 100, 1) if income > 0 else 0,
        "wants_pct": round(wants / income * 100, 1) if income > 0 else 0,
        "savings_pct": round(savings / income * 100, 1) if income > 0 else 0,
        "ideal": {"needs": 50, "wants": 30, "savings": 20},
    }


def generate_suggestions() -> List[Dict]:
    """Generate personalized expense reduction suggestions."""
    suggestions = []

    # 1. Budget overruns
    budget_status = get_budget_vs_actual()
    for b in budget_status:
        if b["status"] == "over":
            suggestions.append({
                "priority": "high",
                "category": b["category"],
                "type": "budget_overrun",
                "message": f"You've exceeded your {b['category']} budget by {b['category']} "
                           f"({b['utilization_pct']}% used). Consider reducing spending here.",
                "potential_saving": round(b["spent"] - b["budget"], 2),
            })
        elif b["status"] == "warning":
            suggestions.append({
                "priority": "medium",
                "category": b["category"],
                "type": "budget_warning",
                "message": f"{b['category']} spending is at {b['utilization_pct']}% of budget. "
                           f"Only {b['category']} {b['remaining']:.0f} remaining.",
            })

    # 2. Top discretionary spending
    discretionary = get_top_discretionary_spending()
    for d in discretionary[:3]:
        cat = d["category"]
        tips = CATEGORY_TIPS.get(cat, [])
        tip = tips[0] if tips else "Review this spending category for savings opportunities."
        suggestions.append({
            "priority": "medium",
            "category": cat,
            "type": "discretionary_spending",
            "message": f"{cat} is one of your top discretionary expenses "
                       f"(total: {d['total']:,.0f}). {tip}",
        })

    # 3. Subscription audit
    subs = get_subscription_audit()
    if subs:
        total_annual = sum(s["estimated_annual"] for s in subs)
        suggestions.append({
            "priority": "medium",
            "category": "Subscriptions",
            "type": "subscription_audit",
            "message": f"You have {len(subs)} recurring subscriptions costing ~{total_annual:,.0f}/year. "
                       f"Review and cancel unused ones.",
            "potential_saving": round(total_annual * 0.2, 2),
        })

    # 4. 50/30/20 analysis
    ratio = get_spending_ratio_analysis()
    if "error" not in ratio:
        if ratio["wants_pct"] > 35:
            suggestions.append({
                "priority": "high",
                "category": "Overall",
                "type": "spending_ratio",
                "message": f"Your discretionary spending ({ratio['wants_pct']}%) exceeds the "
                           f"recommended 30%. Try to redirect some towards savings.",
            })
        if ratio["savings_pct"] < 15:
            suggestions.append({
                "priority": "high",
                "category": "Overall",
                "type": "savings_low",
                "message": f"Your savings rate ({ratio['savings_pct']}%) is below the recommended 20%. "
                           f"Consider automating savings via SIPs or RDs.",
            })

    suggestions.sort(key=lambda s: {"high": 0, "medium": 1, "low": 2}[s["priority"]])
    return suggestions

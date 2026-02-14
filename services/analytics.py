import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from core.database import execute_query
from core.logger import setup_logger

logger = setup_logger("pfa.analytics")


def get_monthly_trends() -> List[Dict]:
    """Monthly income, expenses, savings with rolling averages."""
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
    if not rows:
        return []

    data = [dict(r) for r in rows]
    expenses = [d["expenses"] for d in data]

    # 3-month moving average
    for i, d in enumerate(data):
        window_3 = expenses[max(0, i - 2):i + 1]
        d["expense_ma3"] = round(sum(window_3) / len(window_3), 2)
        window_6 = expenses[max(0, i - 5):i + 1]
        d["expense_ma6"] = round(sum(window_6) / len(window_6), 2)
        d["savings_rate"] = round(
            (d["savings"] / d["income"] * 100) if d["income"] > 0 else 0, 1
        )

    return data


def detect_anomalies(threshold_factor: float = 1.5) -> List[Dict]:
    """
    Find months where category spending spiked above threshold_factor * average.
    """
    rows = execute_query(
        """SELECT
             substr(date, 1, 7) as month,
             category,
             SUM(amount) as total
           FROM daily_transactions
           WHERE transaction_type = 'Debit'
           GROUP BY substr(date, 1, 7), category
           ORDER BY month""",
        fetch=True,
    )
    if not rows:
        return []

    # Compute average per category
    cat_totals: Dict[str, List[float]] = {}
    month_cat: Dict[str, Dict[str, float]] = {}
    for r in rows:
        cat = r["category"] or "Uncategorized"
        cat_totals.setdefault(cat, []).append(r["total"])
        month_cat.setdefault(r["month"], {})[cat] = r["total"]

    cat_avg = {cat: sum(vals) / len(vals) for cat, vals in cat_totals.items()}

    anomalies = []
    for month, cats in month_cat.items():
        for cat, total in cats.items():
            avg = cat_avg.get(cat, 0)
            if avg > 0 and total > avg * threshold_factor:
                anomalies.append({
                    "month": month,
                    "category": cat,
                    "amount": round(total, 2),
                    "average": round(avg, 2),
                    "spike_pct": round((total / avg - 1) * 100, 1),
                })

    return anomalies


def forecast_next_month() -> Dict:
    """
    Simple linear trend forecast for next month's expenses and income.
    """
    rows = execute_query(
        """SELECT
             substr(date, 1, 7) as month,
             SUM(CASE WHEN transaction_type='Credit' THEN amount ELSE 0 END) as income,
             SUM(CASE WHEN transaction_type='Debit' THEN amount ELSE 0 END) as expenses
           FROM daily_transactions
           GROUP BY substr(date, 1, 7)
           ORDER BY month""",
        fetch=True,
    )
    if not rows or len(rows) < 2:
        return {"error": "Need at least 2 months of data for forecasting"}

    data = [dict(r) for r in rows]
    n = len(data)
    x = np.arange(n)

    expenses = np.array([d["expenses"] for d in data])
    income = np.array([d["income"] for d in data])

    # Linear regression
    exp_slope, exp_intercept = np.polyfit(x, expenses, 1)
    inc_slope, inc_intercept = np.polyfit(x, income, 1)

    next_x = n
    forecast_expenses = max(0, exp_slope * next_x + exp_intercept)
    forecast_income = max(0, inc_slope * next_x + inc_intercept)

    return {
        "forecast_expenses": round(forecast_expenses, 2),
        "forecast_income": round(forecast_income, 2),
        "expense_trend": "increasing" if exp_slope > 0 else "decreasing",
        "income_trend": "increasing" if inc_slope > 0 else "decreasing",
        "expense_change_per_month": round(exp_slope, 2),
        "income_change_per_month": round(inc_slope, 2),
        "months_analyzed": n,
    }


def get_category_growth_rates() -> List[Dict]:
    """Identify which expense categories are growing fastest."""
    rows = execute_query(
        """SELECT
             substr(date, 1, 7) as month,
             category,
             SUM(amount) as total
           FROM daily_transactions
           WHERE transaction_type = 'Debit' AND category IS NOT NULL
           GROUP BY substr(date, 1, 7), category
           ORDER BY month""",
        fetch=True,
    )
    if not rows:
        return []

    cat_monthly: Dict[str, List[float]] = {}
    for r in rows:
        cat_monthly.setdefault(r["category"], []).append(r["total"])

    growth_rates = []
    for cat, values in cat_monthly.items():
        if len(values) < 2:
            continue
        first_half = sum(values[:len(values) // 2])
        second_half = sum(values[len(values) // 2:])
        if first_half > 0:
            growth = ((second_half - first_half) / first_half) * 100
        else:
            growth = 100.0 if second_half > 0 else 0.0
        growth_rates.append({
            "category": cat,
            "growth_pct": round(growth, 1),
            "recent_avg": round(second_half / max(1, len(values) - len(values) // 2), 2),
        })

    growth_rates.sort(key=lambda x: x["growth_pct"], reverse=True)
    return growth_rates


def get_seasonal_patterns() -> List[Dict]:
    """Identify spending patterns by calendar month across years."""
    rows = execute_query(
        """SELECT
             CAST(substr(date, 6, 2) AS INTEGER) as cal_month,
             AVG(amount) as avg_daily_spend,
             SUM(amount) as total_spend,
             COUNT(*) as txn_count
           FROM daily_transactions
           WHERE transaction_type = 'Debit'
           GROUP BY CAST(substr(date, 6, 2) AS INTEGER)
           ORDER BY cal_month""",
        fetch=True,
    )
    if not rows:
        return []

    data = [dict(r) for r in rows]
    overall_avg = sum(d["total_spend"] for d in data) / len(data) if data else 1

    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    for d in data:
        d["month_name"] = month_names[d["cal_month"]] if d["cal_month"] <= 12 else "Unknown"
        d["vs_average_pct"] = round((d["total_spend"] / overall_avg - 1) * 100, 1)
        d["avg_daily_spend"] = round(d["avg_daily_spend"], 2)

    return data

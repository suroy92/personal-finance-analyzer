from datetime import datetime, timedelta
from typing import List, Dict

from core.database import execute_query
from core.config import get_config
from core.logger import setup_logger

logger = setup_logger("pfa.festivals")


def get_all_festivals() -> List[Dict]:
    rows = execute_query(
        "SELECT * FROM festivals WHERE is_active = 1 ORDER BY month, day",
        fetch=True,
    )
    return [dict(r) for r in rows] if rows else []


def add_festival(name: str, month: int, day: int, duration_days: int = 1):
    execute_query(
        "INSERT INTO festivals (name, month, day, duration_days) VALUES (?, ?, ?, ?)",
        (name, month, day, duration_days),
    )
    logger.info("Festival added: %s (%d/%d)", name, day, month)


def remove_festival(festival_id: int):
    execute_query("UPDATE festivals SET is_active = 0 WHERE id = ?", (festival_id,))


def get_upcoming_festivals(days_ahead: int = None) -> List[Dict]:
    """Get festivals coming up within the configured alert window."""
    if days_ahead is None:
        cfg = get_config()
        days_ahead = cfg.get("festivals", {}).get("alert_days_before", 21)

    today = datetime.now()
    current_year = today.year
    festivals = get_all_festivals()
    upcoming = []

    for f in festivals:
        try:
            festival_date = datetime(current_year, f["month"], f["day"])
        except ValueError:
            continue

        # If festival has passed this year, check next year
        if festival_date < today:
            festival_date = datetime(current_year + 1, f["month"], f["day"])

        days_until = (festival_date - today).days

        if 0 <= days_until <= days_ahead:
            historical = _get_historical_festival_spending(f["name"], f["month"])
            upcoming.append({
                "name": f["name"],
                "date": festival_date.strftime("%Y-%m-%d"),
                "days_until": days_until,
                "duration_days": f["duration_days"],
                "historical_avg_spend": historical["avg_spend"],
                "suggested_saving": historical["suggested_saving"],
                "message": _build_alert_message(f["name"], days_until, historical),
            })

    upcoming.sort(key=lambda x: x["days_until"])
    return upcoming


def _get_historical_festival_spending(festival_name: str, festival_month: int) -> Dict:
    """Analyze past spending during the festival month vs normal months."""
    # Get average spending in the festival month
    festival_rows = execute_query(
        """SELECT AVG(monthly_total) as avg_spend FROM (
               SELECT substr(date, 1, 7) as month, SUM(amount) as monthly_total
               FROM daily_transactions
               WHERE transaction_type = 'Debit'
                 AND CAST(substr(date, 6, 2) AS INTEGER) = ?
               GROUP BY substr(date, 1, 7)
           )""",
        (festival_month,),
        fetch=True,
    )

    # Get average spending across all months
    overall_rows = execute_query(
        """SELECT AVG(monthly_total) as avg_spend FROM (
               SELECT substr(date, 1, 7) as month, SUM(amount) as monthly_total
               FROM daily_transactions
               WHERE transaction_type = 'Debit'
               GROUP BY substr(date, 1, 7)
           )""",
        fetch=True,
    )

    festival_avg = festival_rows[0]["avg_spend"] if festival_rows and festival_rows[0]["avg_spend"] else 0
    overall_avg = overall_rows[0]["avg_spend"] if overall_rows and overall_rows[0]["avg_spend"] else 0

    extra_spend = max(0, festival_avg - overall_avg)

    return {
        "avg_spend": round(festival_avg, 2),
        "normal_avg": round(overall_avg, 2),
        "extra_spend": round(extra_spend, 2),
        "suggested_saving": round(extra_spend * 1.1, 2),  # 10% buffer
    }


def _build_alert_message(name: str, days_until: int, historical: Dict) -> str:
    cfg = get_config()
    symbol = cfg.get("currency", {}).get("symbol", "\u20B9")

    if days_until == 0:
        time_str = "is today"
    elif days_until == 1:
        time_str = "is tomorrow"
    else:
        time_str = f"is in {days_until} days"

    msg = f"{name} {time_str}!"

    if historical["avg_spend"] > 0:
        msg += (
            f" Based on your history, you typically spend around "
            f"{symbol}{historical['avg_spend']:,.0f} during this period"
        )
        if historical["extra_spend"] > 0:
            msg += (
                f" ({symbol}{historical['extra_spend']:,.0f} more than normal months). "
                f"Consider saving {symbol}{historical['suggested_saving']:,.0f} extra."
            )
        else:
            msg += "."
    else:
        msg += " Plan ahead and set aside some extra savings for festive expenses."

    return msg


def get_festive_spending_analysis() -> List[Dict]:
    """Compare spending in festive months vs non-festive months."""
    festivals = get_all_festivals()
    festive_months = set(f["month"] for f in festivals)

    rows = execute_query(
        """SELECT
             CAST(substr(date, 6, 2) AS INTEGER) as cal_month,
             substr(date, 1, 7) as year_month,
             SUM(amount) as total_spend
           FROM daily_transactions
           WHERE transaction_type = 'Debit'
           GROUP BY substr(date, 1, 7)
           ORDER BY year_month""",
        fetch=True,
    )
    if not rows:
        return []

    festive_totals = []
    normal_totals = []
    for r in rows:
        if r["cal_month"] in festive_months:
            festive_totals.append(r["total_spend"])
        else:
            normal_totals.append(r["total_spend"])

    festive_avg = sum(festive_totals) / len(festive_totals) if festive_totals else 0
    normal_avg = sum(normal_totals) / len(normal_totals) if normal_totals else 0

    return {
        "festive_months_avg": round(festive_avg, 2),
        "normal_months_avg": round(normal_avg, 2),
        "difference": round(festive_avg - normal_avg, 2),
        "difference_pct": round(
            ((festive_avg - normal_avg) / normal_avg * 100) if normal_avg > 0 else 0, 1
        ),
        "festive_months_count": len(festive_totals),
        "normal_months_count": len(normal_totals),
    }

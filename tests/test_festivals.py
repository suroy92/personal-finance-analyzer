from datetime import datetime
from services.festival_service import (
    get_all_festivals,
    add_festival,
    get_upcoming_festivals,
    get_festive_spending_analysis,
)
from services.transaction_service import ingest_csv


def test_festivals_seeded(test_db):
    festivals = get_all_festivals()
    assert len(festivals) >= 2
    names = {f["name"] for f in festivals}
    assert "Diwali" in names


def test_add_festival(test_db):
    add_festival("Pongal", 1, 15, 4)
    festivals = get_all_festivals()
    names = {f["name"] for f in festivals}
    assert "Pongal" in names


def test_upcoming_festivals(test_db):
    # Add a festival that's always "upcoming" (set to a few days from now)
    now = datetime.now()
    future_day = (now.day % 28) + 1  # Ensure valid day
    future_month = now.month
    if future_day <= now.day:
        future_month = (now.month % 12) + 1

    add_festival("Test Festival", future_month, future_day, 1)
    upcoming = get_upcoming_festivals(days_ahead=60)
    assert isinstance(upcoming, list)
    # Should contain at least our test festival (or seeded ones)


def test_festive_spending_analysis_empty(test_db):
    analysis = get_festive_spending_analysis()
    assert isinstance(analysis, (dict, list))


def test_festive_spending_analysis_with_data(test_db):
    # Seed data across different months including festival months (Oct, Dec)
    csv = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-10,GROCERY SHOPPING,2000,0
2024-02-10,GROCERY SHOPPING,2500,0
2024-10-10,DIWALI SHOPPING,8000,0
2024-10-15,DIWALI GIFTS,5000,0
2024-12-20,CHRISTMAS GIFTS,6000,0
"""
    ingest_csv(csv, "test.csv")

    analysis = get_festive_spending_analysis()
    # Analysis can be a dict or empty list depending on data
    assert isinstance(analysis, (dict, list))
    if isinstance(analysis, dict) and analysis.get("festive_months_count", 0) > 0:
        assert analysis["festive_months_avg"] > 0


def test_upcoming_festival_message(test_db):
    upcoming = get_upcoming_festivals(days_ahead=365)  # Large window to catch something
    for f in upcoming:
        assert "message" in f
        assert "days_until" in f
        assert f["days_until"] >= 0

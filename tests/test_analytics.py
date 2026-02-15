from services.transaction_service import ingest_csv
from services.analytics import (
    get_monthly_trends,
    detect_anomalies,
    forecast_next_month,
    get_category_growth_rates,
    get_seasonal_patterns,
)


def _seed_multi_month_data(test_db):
    csv = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-05,SALARY CREDIT,0,50000
2024-01-10,ZOMATO ORDER,500,0
2024-01-15,AMAZON PURCHASE,3000,0
2024-01-20,SIP MUTUAL FUND,5000,0
2024-02-05,SALARY CREDIT,0,52000
2024-02-10,SWIGGY ORDER,600,0
2024-02-15,FLIPKART PURCHASE,4000,0
2024-02-20,SIP MUTUAL FUND,5000,0
2024-03-05,SALARY CREDIT,0,53000
2024-03-10,ZOMATO ORDER,800,0
2024-03-15,AMAZON PURCHASE,2000,0
2024-03-20,SIP MUTUAL FUND,5000,0
"""
    ingest_csv(csv, "test.csv")


def test_monthly_trends(test_db):
    _seed_multi_month_data(test_db)
    trends = get_monthly_trends()
    assert len(trends) == 3
    assert "expense_ma3" in trends[0]
    assert "expense_ma6" in trends[0]
    assert "savings_rate" in trends[0]


def test_monthly_trends_empty(test_db):
    trends = get_monthly_trends()
    assert trends == []


def test_detect_anomalies(test_db):
    _seed_multi_month_data(test_db)
    anomalies = detect_anomalies(threshold_factor=1.0)
    # With varied spending, some anomalies should be detected
    assert isinstance(anomalies, list)


def test_forecast_insufficient_data(test_db):
    csv = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-15,ZOMATO ORDER,500,0
"""
    ingest_csv(csv, "test.csv")
    forecast = forecast_next_month()
    assert "error" in forecast


def test_forecast_with_data(test_db):
    _seed_multi_month_data(test_db)
    forecast = forecast_next_month()
    assert "forecast_expenses" in forecast
    assert "forecast_income" in forecast
    assert forecast["months_analyzed"] == 3
    assert forecast["forecast_expenses"] > 0


def test_category_growth_rates(test_db):
    _seed_multi_month_data(test_db)
    rates = get_category_growth_rates()
    assert isinstance(rates, list)
    if rates:
        assert "category" in rates[0]
        assert "growth_pct" in rates[0]


def test_seasonal_patterns(test_db):
    _seed_multi_month_data(test_db)
    patterns = get_seasonal_patterns()
    assert len(patterns) >= 1
    assert "month_name" in patterns[0]
    assert "vs_average_pct" in patterns[0]

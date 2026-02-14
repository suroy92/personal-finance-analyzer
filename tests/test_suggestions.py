from services.suggestion_service import (
    get_top_discretionary_spending,
    what_if_calculator,
    get_spending_ratio_analysis,
    generate_suggestions,
)
from services.budget_service import set_budget
from services.transaction_service import ingest_csv


def _seed_data(test_db):
    csv = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-05,SALARY CREDIT,0,50000
2024-01-10,ZOMATO ORDER,2000,0
2024-01-12,SWIGGY ORDER,1500,0
2024-01-15,AMAZON PURCHASE,5000,0
2024-01-18,NETFLIX SUBSCRIPTION,500,0
2024-01-20,SIP MUTUAL FUND,5000,0
2024-01-25,UBER RIDE,800,0
2024-02-05,SALARY CREDIT,0,50000
2024-02-10,ZOMATO ORDER,2500,0
2024-02-15,AMAZON PURCHASE,3000,0
2024-02-20,SIP MUTUAL FUND,5000,0
"""
    ingest_csv(csv, "test.csv")


def test_top_discretionary_spending(test_db):
    _seed_data(test_db)
    result = get_top_discretionary_spending()
    assert len(result) >= 1
    categories = {r["category"] for r in result}
    assert "Food & Dining" in categories


def test_what_if_calculator(test_db):
    _seed_data(test_db)
    result = what_if_calculator("Food & Dining", 20)
    assert "annual_saving" in result
    assert result["reduction_pct"] == 20
    assert result["monthly_saving"] > 0
    assert result["annual_saving"] == result["monthly_saving"] * 12


def test_what_if_calculator_no_data(test_db):
    result = what_if_calculator("Nonexistent Category", 10)
    assert "error" in result


def test_spending_ratio_analysis(test_db):
    _seed_data(test_db)
    ratio = get_spending_ratio_analysis()
    assert "needs_pct" in ratio
    assert "wants_pct" in ratio
    assert "savings_pct" in ratio
    assert ratio["income"] == 100000


def test_generate_suggestions(test_db):
    _seed_data(test_db)
    set_budget("Food & Dining", 2000)

    suggestions = generate_suggestions()
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    assert all("message" in s for s in suggestions)
    assert all("priority" in s for s in suggestions)

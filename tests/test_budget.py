from services.budget_service import (
    set_budget,
    get_all_budgets,
    delete_budget,
    get_budget_vs_actual,
    apply_50_30_20_rule,
)
from services.transaction_service import ingest_csv


def test_set_and_get_budget(test_db):
    set_budget("Food & Dining", 5000)
    budgets = get_all_budgets()
    assert len(budgets) == 1
    assert budgets[0]["category"] == "Food & Dining"
    assert budgets[0]["monthly_limit"] == 5000


def test_update_budget(test_db):
    set_budget("Food & Dining", 5000)
    set_budget("Food & Dining", 7000)
    budgets = get_all_budgets()
    assert len(budgets) == 1
    assert budgets[0]["monthly_limit"] == 7000


def test_delete_budget(test_db):
    set_budget("Shopping", 3000)
    delete_budget("Shopping")
    budgets = get_all_budgets()
    assert len(budgets) == 0


def test_budget_vs_actual(test_db):
    csv = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-10,ZOMATO ORDER,500,0
2024-01-12,SWIGGY ORDER,300,0
"""
    ingest_csv(csv, "test.csv")
    set_budget("Food & Dining", 1000)

    results = get_budget_vs_actual("2024-01")
    assert len(results) == 1
    assert results[0]["category"] == "Food & Dining"
    assert results[0]["spent"] == 800
    assert results[0]["remaining"] == 200
    assert results[0]["status"] in ("warning", "ok")  # 80% is at boundary


def test_budget_vs_actual_over(test_db):
    csv = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-10,ZOMATO ORDER,600,0
2024-01-12,SWIGGY ORDER,500,0
"""
    ingest_csv(csv, "test.csv")
    set_budget("Food & Dining", 1000)

    results = get_budget_vs_actual("2024-01")
    assert results[0]["status"] == "over"


def test_50_30_20_rule():
    result = apply_50_30_20_rule(100000)
    assert result["needs"] == 50000
    assert result["wants"] == 30000
    assert result["savings"] == 20000

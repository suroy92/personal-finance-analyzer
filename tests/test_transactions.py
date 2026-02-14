import io
import pytest
from services.transaction_service import (
    preprocess_description,
    label_with_keywords,
    classify_transaction,
    ingest_csv,
    get_summary,
    get_monthly_breakdown,
    get_category_breakdown,
    update_transaction_category,
)


def test_preprocess_description():
    assert preprocess_description("Zomato Order-110889182110") == "ZOMATO ORDER"
    assert preprocess_description("  hello   world  ") == "HELLO WORLD"
    assert preprocess_description(None) == ""
    assert preprocess_description("") == ""


def test_label_with_keywords_expense():
    txn_type, cat = label_with_keywords("ZOMATO ORDER 123")
    assert txn_type == "Expense"
    assert cat == "Food & Dining"


def test_label_with_keywords_savings():
    txn_type, cat = label_with_keywords("SIP MUTUAL FUND INVESTNOWIP")
    assert txn_type == "Savings/Investment"
    assert cat == "Mutual Fund SIP"


def test_label_with_keywords_income():
    txn_type, cat = label_with_keywords("SALARY CREDIT HR DEPT")
    assert txn_type == "Income"
    assert cat == "Salary"


def test_label_with_keywords_unknown():
    txn_type, cat = label_with_keywords("RANDOM TRANSACTION XYZ")
    assert txn_type is None
    assert cat is None


def test_classify_credit(test_db):
    txn_type, cat, is_saving = classify_transaction("SALARY CREDIT", 50000, is_credit=True)
    assert txn_type == "Credit"
    assert cat == "Salary"
    assert is_saving == 0


def test_classify_debit_expense(test_db):
    txn_type, cat, is_saving = classify_transaction("ZOMATO ORDER", 500, is_credit=False)
    assert txn_type == "Debit"
    assert cat == "Food & Dining"
    assert is_saving == 0


def test_classify_debit_saving(test_db):
    txn_type, cat, is_saving = classify_transaction("SIP MUTUAL FUND", 5000, is_credit=False)
    assert txn_type == "Debit"
    assert cat == "Mutual Fund SIP"
    assert is_saving == 1


def test_ingest_csv(test_db):
    csv_content = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-15,ZOMATO ORDER,500,0
2024-01-16,SALARY CREDIT,0,50000
2024-01-17,SIP MUTUAL FUND,5000,0
2024-01-18,RANDOM PURCHASE,1000,0
"""
    result = ingest_csv(csv_content, "test.csv")
    assert result["total_rows"] == 4
    assert result["inserted"] == 4
    assert result["skipped"] == 0


def test_ingest_csv_duplicates(test_db):
    csv_content = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-15,ZOMATO ORDER,500,0
"""
    result1 = ingest_csv(csv_content, "test.csv")
    assert result1["inserted"] == 1

    result2 = ingest_csv(csv_content, "test.csv")
    assert result2["inserted"] == 0
    assert result2["skipped"] == 1


def test_ingest_csv_missing_columns(test_db):
    csv_content = b"""Date,Description,Amount
2024-01-15,ZOMATO,500
"""
    with pytest.raises(ValueError, match="missing required columns"):
        ingest_csv(csv_content, "test.csv")


def test_get_summary(test_db):
    csv_content = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-15,ZOMATO ORDER,500,0
2024-01-16,SALARY CREDIT,0,50000
"""
    ingest_csv(csv_content, "test.csv")

    summary = get_summary()
    assert summary["total_income"] == 50000
    assert summary["total_expenses"] == 500
    assert summary["total_count"] == 2


def test_get_monthly_breakdown(test_db):
    csv_content = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-15,ZOMATO ORDER,500,0
2024-02-15,AMAZON PURCHASE,1000,0
"""
    ingest_csv(csv_content, "test.csv")

    breakdown = get_monthly_breakdown()
    assert len(breakdown) == 2
    assert breakdown[0]["month"] == "2024-01"
    assert breakdown[1]["month"] == "2024-02"


def test_get_category_breakdown(test_db):
    csv_content = b"""Date,Narration,Debit Amount,Credit Amount
2024-01-15,ZOMATO ORDER,500,0
2024-01-16,SWIGGY ORDER,300,0
2024-01-17,AMAZON PURCHASE,2000,0
"""
    ingest_csv(csv_content, "test.csv")

    breakdown = get_category_breakdown("Debit")
    assert len(breakdown) >= 2
    categories = {b["category"] for b in breakdown}
    assert "Food & Dining" in categories
    assert "Shopping" in categories

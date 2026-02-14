from core.database import execute_query
from models.ml_models import (
    train_models,
    predict_debit_type,
    predict_expense_category,
    predict_savings_category,
)


def _seed_training_data(test_db):
    samples = [
        ("ZOMATO ORDER", "Food & Dining"),
        ("SWIGGY DELIVERY", "Food & Dining"),
        ("STARBUCKS COFFEE", "Food & Dining"),
        ("AMAZON PURCHASE", "Shopping"),
        ("FLIPKART ORDER", "Shopping"),
        ("MYNTRA FASHION", "Shopping"),
        ("UBER RIDE", "Transportation"),
        ("OLA CAB", "Transportation"),
        ("SIP MUTUAL FUND", "Mutual Fund SIP"),
        ("LIC PREMIUM", "Insurance"),
        ("FIXED DEPOSIT FD", "Fixed Deposit"),
        ("NETFLIX SUBSCRIPTION", "Subscriptions"),
        ("SPOTIFY PREMIUM", "Subscriptions"),
    ]
    for desc, cat in samples:
        execute_query(
            "INSERT INTO training_data (description, category) VALUES (?, ?)",
            (desc, cat),
        )


def test_train_models_no_data(test_db):
    # Should not crash with no data
    train_models()


def test_train_and_predict(test_db):
    _seed_training_data(test_db)
    train_models()

    label, conf = predict_debit_type("ZOMATO ORDER NEW")
    assert label in ("Expense", "Savings/Investment")
    assert 0 <= conf <= 1

    label, conf = predict_expense_category("AMAZON SHOPPING")
    assert label is not None
    assert 0 <= conf <= 1

    label, conf = predict_savings_category("SIP MUTUAL FUND PURCHASE")
    assert label is not None
    assert 0 <= conf <= 1


def test_predict_without_training(test_db):
    label, conf = predict_debit_type("SOMETHING RANDOM")
    assert label is None
    assert conf == 0.0

# ml_models.py
from typing import Tuple, Optional, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from database import execute_query
from keywords import SAVINGS_KEYWORDS  # to know what counts as "Savings/Investment"

# -----------------------
# Global model state
# -----------------------
_debit_type_model: Optional[LogisticRegression] = None
_expense_model: Optional[LogisticRegression] = None
_savings_model: Optional[LogisticRegression] = None
_vectorizer: Optional[TfidfVectorizer] = None

# Canonical list of savings categories (keys in SAVINGS_KEYWORDS)
_SAVINGS_CATEGORIES: List[str] = list(SAVINGS_KEYWORDS.keys())


def _has_training_data() -> bool:
    rows = execute_query("SELECT COUNT(*) FROM training_data", fetch=True)
    return bool(rows and rows[0][0] > 0)


def _ensure_trained() -> None:
    """
    Train once lazily if models are missing but training data exists.
    Safe to call before any prediction.
    """
    global _debit_type_model, _expense_model, _savings_model, _vectorizer
    if any(m is None for m in [_debit_type_model, _expense_model, _savings_model, _vectorizer]) and _has_training_data():
        train_models()


def train_models() -> None:
    """
    Trains/refreshes all models from the training_data table using execute_query().
    """
    global _debit_type_model, _expense_model, _savings_model, _vectorizer

    data = execute_query("SELECT description, category FROM training_data", fetch=True)
    if not data:
        # nothing to train on
        _debit_type_model = _expense_model = _savings_model = _vectorizer = None
        return

    descriptions = [row[0] for row in data]
    categories = [row[1] for row in data]

    _vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    X = _vectorizer.fit_transform(descriptions)

    # Debit type model: Expense vs Savings/Investment
    y_debit_type = ["Savings/Investment" if c in _SAVINGS_CATEGORIES else "Expense" for c in categories]
    _debit_type_model = LogisticRegression(max_iter=600)
    _debit_type_model.fit(X, y_debit_type)

    # Expense category model (map savings categories to "Other" so they don’t pollute expense labels)
    expense_labels = [c if c not in _SAVINGS_CATEGORIES else "Other" for c in categories]
    _expense_model = LogisticRegression(max_iter=600)
    _expense_model.fit(X, expense_labels)

    # Savings category model (map non-savings to "Other")
    savings_labels = [c if c in _SAVINGS_CATEGORIES else "Other" for c in categories]
    _savings_model = LogisticRegression(max_iter=600)
    _savings_model.fit(X, savings_labels)


def _predict_generic(model: Optional[LogisticRegression], text: str) -> Tuple[Optional[str], float]:
    """
    Utility: returns (label, confidence).
    """
    if model is None or _vectorizer is None:
        return None, 0.0
    X = _vectorizer.transform([text])
    label = model.predict(X)[0]
    conf = float(max(model.predict_proba(X)[0]))
    return label, conf


def predict_debit_type(description: str) -> Tuple[Optional[str], float]:
    """
    Returns ("Expense" or "Savings/Investment", confidence).
    """
    _ensure_trained()
    return _predict_generic(_debit_type_model, description)


def predict_expense_category(description: str) -> Tuple[Optional[str], float]:
    """
    Returns (expense_category_label, confidence).
    """
    _ensure_trained()
    return _predict_generic(_expense_model, description)


def predict_savings_category(description: str) -> Tuple[Optional[str], float]:
    """
    Returns (savings_category_label, confidence).
    """
    _ensure_trained()
    return _predict_generic(_savings_model, description)

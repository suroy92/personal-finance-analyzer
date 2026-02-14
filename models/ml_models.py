import os
import threading
import hashlib
import joblib
from typing import Tuple, Optional, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from core.config import get_config
from core.database import execute_query
from core.logger import setup_logger
from models.keywords import ALL_SAVINGS_CATEGORIES

logger = setup_logger("pfa.ml")

_lock = threading.Lock()

_debit_type_model: Optional[LogisticRegression] = None
_expense_model: Optional[LogisticRegression] = None
_savings_model: Optional[LogisticRegression] = None
_vectorizer: Optional[TfidfVectorizer] = None
_data_hash: Optional[str] = None


def _model_dir():
    cfg = get_config()
    path = cfg.get("ml", {}).get("model_save_path", "saved_models/")
    os.makedirs(path, exist_ok=True)
    return path


def _compute_data_hash(data):
    raw = "".join(f"{d}|{c}" for d, c in data)
    return hashlib.md5(raw.encode()).hexdigest()


def _save_models():
    path = _model_dir()
    joblib.dump(_vectorizer, os.path.join(path, "vectorizer.joblib"))
    joblib.dump(_debit_type_model, os.path.join(path, "debit_type.joblib"))
    joblib.dump(_expense_model, os.path.join(path, "expense.joblib"))
    joblib.dump(_savings_model, os.path.join(path, "savings.joblib"))
    if _data_hash:
        with open(os.path.join(path, "data_hash.txt"), "w") as f:
            f.write(_data_hash)
    logger.info("Models saved to %s", path)


def _load_models():
    global _debit_type_model, _expense_model, _savings_model, _vectorizer, _data_hash
    path = _model_dir()
    vect_path = os.path.join(path, "vectorizer.joblib")
    if not os.path.exists(vect_path):
        return False
    try:
        _vectorizer = joblib.load(vect_path)
        _debit_type_model = joblib.load(os.path.join(path, "debit_type.joblib"))
        _expense_model = joblib.load(os.path.join(path, "expense.joblib"))
        _savings_model = joblib.load(os.path.join(path, "savings.joblib"))
        hash_path = os.path.join(path, "data_hash.txt")
        if os.path.exists(hash_path):
            with open(hash_path) as f:
                _data_hash = f.read().strip()
        logger.info("Models loaded from disk")
        return True
    except Exception as e:
        logger.warning("Failed to load models: %s", e)
        return False


def train_models():
    global _debit_type_model, _expense_model, _savings_model, _vectorizer, _data_hash

    rows = execute_query("SELECT description, category FROM training_data", fetch=True)
    if not rows:
        logger.info("No training data available, skipping training")
        return

    data = [(row["description"], row["category"]) for row in rows]
    new_hash = _compute_data_hash(data)

    with _lock:
        if _data_hash == new_hash:
            logger.info("Training data unchanged, skipping retrain")
            return

        descriptions = [d for d, _ in data]
        categories = [c for _, c in data]

        _vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        X = _vectorizer.fit_transform(descriptions)

        # Debit type: Expense vs Savings/Investment
        y_debit = [
            "Savings/Investment" if c in ALL_SAVINGS_CATEGORIES else "Expense"
            for c in categories
        ]
        if len(set(y_debit)) >= 2:
            _debit_type_model = LogisticRegression(max_iter=600)
            _debit_type_model.fit(X, y_debit)
        else:
            _debit_type_model = None
            logger.info("Skipping debit-type model: only one class in data")

        # Expense category
        expense_labels = [c if c not in ALL_SAVINGS_CATEGORIES else "Other" for c in categories]
        if len(set(expense_labels)) >= 2:
            _expense_model = LogisticRegression(max_iter=600)
            _expense_model.fit(X, expense_labels)
        else:
            _expense_model = None

        # Savings category
        savings_labels = [c if c in ALL_SAVINGS_CATEGORIES else "Other" for c in categories]
        if len(set(savings_labels)) >= 2:
            _savings_model = LogisticRegression(max_iter=600)
            _savings_model.fit(X, savings_labels)
        else:
            _savings_model = None

        _data_hash = new_hash
        _save_models()
        logger.info("Models trained on %d examples", len(data))


def _ensure_trained():
    global _debit_type_model
    if _debit_type_model is None:
        with _lock:
            if _debit_type_model is None:
                if not _load_models():
                    rows = execute_query("SELECT COUNT(*) as cnt FROM training_data", fetch=True)
                    if rows and rows[0]["cnt"] > 0:
                        _lock.release()
                        try:
                            train_models()
                        finally:
                            _lock.acquire()


def _predict_generic(model, text: str) -> Tuple[Optional[str], float]:
    if model is None or _vectorizer is None:
        return None, 0.0
    with _lock:
        X = _vectorizer.transform([text])
        label = model.predict(X)[0]
        conf = float(max(model.predict_proba(X)[0]))
    return label, conf


def predict_debit_type(description: str) -> Tuple[Optional[str], float]:
    _ensure_trained()
    return _predict_generic(_debit_type_model, description)


def predict_expense_category(description: str) -> Tuple[Optional[str], float]:
    _ensure_trained()
    return _predict_generic(_expense_model, description)


def predict_savings_category(description: str) -> Tuple[Optional[str], float]:
    _ensure_trained()
    return _predict_generic(_savings_model, description)

# 💰 # # Personal Finance Analyzer

A desktop app that helps you import bank statements, auto-classify transactions (income, expenses, savings/investments), visualize spending, and continuously improve via lightweight machine-learning — all on your local machine.

Built with Python, Tkinter, SQLite, pandas, matplotlib, and scikit-learn.

---

## ✨ Features

* **One-click CSV import**: Load a bank statement and the app parses, normalizes, and stores each transaction. Required columns: `Date`, `Narration`, `Debit Amount`, `Credit Amount`. 
* **Smart categorization**:

  * Keyword heuristics for common merchants and terms (e.g., Food & Dining, Groceries, Subscriptions). 
  * ML models predict debit type (Expense vs. Savings/Investment) and fine-grained categories, with gentle confidence gating. 
* **Human-in-the-loop labeling**: Clean dropdowns let you correct or choose categories; your choices are saved as training data. 
* **Always-on learning**: New labels trigger background retraining so the model gets better with your data. 
* **Dashboard & charts**: Quick totals for credits, debits, and savings, plus category bar charts for spend vs. income. 
* **Local & private**: Data lives in a local SQLite database (`personal_finance_analyzer.db`). 

---

## 🧱 Architecture Overview

```
main.py            # App entrypoint (Tkinter main loop)
app.py             # GUI, CSV ingest, heuristics, charts, training triggers
database.py        # SQLite schema and query helper
keywords.py        # Keyword dictionaries for bootstrap labeling
ml_models.py       # TF-IDF + Logistic Regression models and predictors
```

* **GUI & Flow**: Tkinter app with buttons for uploading CSV, showing dashboards/charts, and retraining on demand. CSV rows are normalized and inserted into the DB. 
* **Storage**: Two tables:

  * `daily_transactions(id, date, description, amount, transaction_type, category, is_saving, uploaded_at)`
  * `training_data(id, description, category)`
    Created on first run if missing. 
* **Preprocessing**: Narrations are upper-cased, long numeric tails like `-110889182110` are stripped, and whitespace is collapsed. 
* **Heuristics**: Income/Expense/Savings keyword maps seed labels before ML (e.g., Zomato → Food & Dining, SIP → Mutual Fund SIP). 
* **Models**:

  * Shared **TF-IDF** vectorizer (1–2-gram).
  * Three **Logistic Regression** classifiers:

    1. Debit type (Expense vs Savings/Investment),
    2. Expense category,
    3. Savings category.
       Training reads your `training_data` and maps categories appropriately (e.g., non-savings → “Other” for savings model). 

**Entrypoint:** `python main.py` builds the Tk window and starts the app. 

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+ recommended
* OS packages for Tkinter (varies by platform)

### Install

```bash
git clone https://github.com/<your-username>/personal-finance-analyzer.git
cd personal-finance-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Minimal `requirements.txt`:

```
pandas
matplotlib
scikit-learn
```

> Notes:
>
> * `tkinter` and `sqlite3` ship with many Python distributions, but some Linux/macOS environments require installing Tk headers via your package manager.

### Run

```bash
python main.py
```

1. Click **“Upload Bank Statement (CSV)”** and select a CSV with columns `Date`, `Narration`, `Debit Amount`, `Credit Amount`. The app normalizes amounts, classifies each row, and asks for a category when needed. 
2. Open **Dashboard** to see totals for Credit, Debit, and Savings/Investments. 
3. Open **Financial Charts** to view bar charts of spend and income by category. 
4. Click **Retrain Models Now** anytime to refresh ML with the latest labels. Training also occurs in the background after new labels are added. 

---

## 📁 Data & Privacy

* All data is stored locally in `personal_finance_analyzer.db` next to the app. Back it up or delete it at will. 
* No network calls, no third-party data syncing. Everything stays on your machine.

---

## 🔍 CSV Expectations & Tips

* **Columns**: `Date`, `Narration`, `Debit Amount`, `Credit Amount` (case-insensitive header trimming is handled). 
* **Normalization**: Amounts are coerced to numeric; non-numeric entries become `0.0`. 
* **Debit vs Credit**:

  * Positive **Credit Amount** → treated as income; you’ll choose an income category if heuristics can’t.
  * Positive **Debit Amount** → first decide **Expense** vs **Savings/Investment**, then choose a category. ML assists both steps. 

---

## 🧠 How the ML Works

* Models are trained from your **`training_data`** — every time you correct or label a transaction, that becomes a training example. 
* A shared **TF-IDF** vectorizer converts descriptions into features (uni/bi-grams). 
* **Confidence thresholding**: predictions below ~0.7 confidence fall back to a friendly dropdown so you stay in control. 
* **Cold start**: on first run, models wait until you add some labels; until then, keyword rules + dropdowns handle classification. 

---

## 🧪 Development

```bash
# Format / lint as you prefer
pytest       # if you add tests
```

Key modules to explore:

* `app.py`: GUI, ingest pipeline, dialogs, charts. 
* `database.py`: schema creation and simple query wrapper. 
* `keywords.py`: tweak these lists to adapt to your region/bank descriptors. 
* `ml_models.py`: model definitions, training loop, and predictors. 
* `main.py`: bootstraps the Tkinter app. 

---

## 🗺️ Roadmap

* CSV schema presets per bank + mapping UI
* Editable category taxonomy
* Monthly/weekly budgeting and goals
* Export to CSV/Excel
* Simple rules engine (e.g., “contains ‘METRO’ → Transportation”) layered above ML

---

## 📄 License

MIT (or your preferred license).

---

## 🙏 Acknowledgments

Thanks to the open-source community behind pandas, matplotlib, scikit-learn, and countless Tkinter examples.

---

### Developer Notes

* Entry command: `python main.py`. 
* DB filename: `personal_finance_analyzer.db`. 
* Preprocess removes long numeric IDs after hyphens in narrations and collapses whitespace. 
* Savings categories are derived from the `SAVINGS_KEYWORDS` keys; these drive the debit-type model mapping. 
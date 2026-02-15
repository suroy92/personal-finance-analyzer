# Personal Finance Analyzer

A web-based personal finance dashboard that imports bank statements, auto-classifies transactions, tracks budgets, provides trend analysis with forecasting, suggests ways to minimize expenses, and alerts you before festive seasons so you can save ahead.

Built with Python, Dash (Plotly), SQLite, pandas, scikit-learn, and Bootstrap.

---

## Features

- **CSV Import** — Drag-and-drop bank statement upload. Parses, normalizes dates, deduplicates, and classifies each transaction automatically.
- **Smart Categorization** — Keyword heuristics for 14 expense, 6 savings, and 6 income categories. ML models (TF-IDF + Logistic Regression) predict when keywords miss, with confidence gating.
- **Interactive Dashboard** — Summary cards, monthly trend charts, expense pie chart, savings rate tracker, and daily spending heatmap.
- **Trend Analysis** — Moving averages (3/6 month), spending anomaly detection, category growth rates, seasonal pattern analysis, and next-month forecasting.
- **Budget Management** — Set per-category monthly budgets, track utilization with progress bars, and get 50/30/20 rule analysis.
- **Savings Suggestions** — Personalized recommendations based on spending patterns, subscription audit, what-if calculator, and category-specific tips.
- **Festive Season Alerts** — Pre-configured festival calendar with countdown notifications, historical festive spending comparison, and monthly saving suggestions.
- **ML Model Persistence** — Models saved to disk with joblib; only retrained when training data changes.
- **Export & Backup** — Export transactions to CSV and download database backups.
- **Local & Private** — All data stays in a local SQLite database. No network calls.

---

## Architecture

```
run.py                      # App entrypoint
config.yaml                 # Configuration (DB, currency, ML, festivals, server)

core/
  config.py                 # YAML config loader
  database.py               # SQLite with thread-local connections, context manager
  logger.py                 # Structured logging

models/
  keywords.py               # Keyword dictionaries for category classification
  ml_models.py              # TF-IDF + Logistic Regression with thread safety

services/
  transaction_service.py    # CSV ingest, classification, CRUD
  analytics.py              # Trends, anomalies, forecasting, seasonal patterns
  budget_service.py         # Budget CRUD, budget vs actual, 50/30/20 rule
  suggestion_service.py     # Personalized savings suggestions, what-if calculator
  festival_service.py       # Festival calendar, alerts, historical analysis

ui/
  app.py                    # Dash app setup with sidebar navigation
  layouts/                  # Page layouts (dashboard, transactions, analytics, etc.)
  callbacks/                # Dash callbacks wiring UI to services

tests/                      # 47 tests across 7 modules
```

---

## Getting Started

### Prerequisites

- Python 3.10+

### Install

```bash
git clone https://github.com/suroy92/personal-finance-analyzer.git
cd personal-finance-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

Open your browser to `http://127.0.0.1:8050`.

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## CSV Format

Your bank statement CSV should have these columns:

| Column | Description |
|--------|-------------|
| `Date` | Transaction date (supports YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, etc.) |
| `Narration` | Transaction description |
| `Debit Amount` | Amount debited (expenses/investments) |
| `Credit Amount` | Amount credited (income) |

---

## Configuration

Edit `config.yaml` to customize:

- **Currency** — symbol, code, locale
- **ML** — confidence threshold, model save path
- **Festivals** — add/remove festivals with dates and durations
- **Server** — host, port, debug mode

---

## Pages

| Page | What it shows |
|------|---------------|
| **Dashboard** | Summary cards, monthly trends, expense breakdown, savings rate, heatmap, forecast, budget status |
| **Transactions** | Searchable/filterable table of all transactions |
| **Analytics** | Moving averages, anomaly detection, growth rates, seasonal patterns, category over time |
| **Budgets** | Set/manage budgets, budget vs actual chart, 50/30/20 analysis |
| **Suggestions** | Personalized tips, what-if calculator, subscription audit, discretionary spending |
| **Festival Alerts** | Upcoming festivals with countdowns, festive vs normal spending, manage festival calendar |
| **Import Data** | CSV upload, CSV export |
| **Settings** | Retrain ML models, database backup |

---

## License

MIT

---

## Roadmap

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for completed and planned improvements.

Items marked for future work:
- PDF statement parsing
- Column mapping UI for different bank formats
- Database encryption (sqlcipher)
- App-level authentication
- Advanced ML features (amount-based features, category taxonomy management)

# Personal Finance Analyzer - Improvements Plan

## 1. Architecture & Code Quality

- [x] 1.1 Consolidate the 3 duplicate versions — removed `personal_finance_analyzer.py` and `personal_finance_analyzer.gui.py`
- [x] 1.2 Adopt a proper project structure — `core/`, `ui/`, `models/`, `data/`, `services/`
- [x] 1.3 Replace Tkinter with Dash (Plotly) web-based UI with interactive dashboard
- [x] 1.4 Add configuration management — `config.yaml` for DB path, thresholds, currency, locale, festivals
- [x] 1.5 Add proper logging — structured logging to file and console via `core/logger.py`
- [x] 1.6 Add unit and integration tests — 47 tests across 7 test modules (all passing)
- [x] 1.7 Thread safety — `threading.Lock` in `models/ml_models.py` protects global model state
- [x] 1.8 DB connection management — thread-local connections with context manager in `core/database.py`

## 2. Database & Data Model

- [x] 2.1 Add a `budgets` table — monthly budget targets per category
- [x] 2.2 Add a `monthly_summary` table — aggregate monthly income/expenses/savings
- [x] 2.3 Add a `festivals` table — store upcoming festivals with date, duration, active flag
- [x] 2.4 Add a `savings_goals` table — target amount, deadline, progress tracking
- [x] 2.5 Add proper date parsing — multi-format parser normalizes to ISO YYYY-MM-DD
- [x] 2.6 Add duplicate detection — SHA-256 hash on (date, description, amount, type) prevents re-imports
- [x] 2.7 Add migration support — `schema_version` table tracks DB schema version

## 3. Dashboard & Visualization

- [x] 3.1 Build a real dashboard panel — 4 summary cards (income, expenses, savings, net position)
- [x] 3.2 Add time-series trend charts — grouped bar chart of monthly income/expenses/savings
- [x] 3.3 Add category breakdown over time — stacked area chart by category per month
- [x] 3.4 Add a calendar heatmap — daily spending intensity by weekday/week
- [x] 3.5 Add income vs expense ratio tracking — savings rate line chart with 20% target

## 4. Trend Analysis & Forecasting

- [x] 4.1 Implement moving averages — 3-month and 6-month rolling averages on analytics page
- [x] 4.2 Spending anomaly detection — flags months where category spending > 1.5x average
- [x] 4.3 Forecasting — linear regression projects next month's expenses and income
- [x] 4.4 Category growth rates — horizontal bar chart showing fastest-growing expense categories
- [x] 4.5 Seasonal pattern detection — bar chart showing each calendar month vs overall average

## 5. Expense Minimization Suggestions

- [x] 5.1 Budget vs actual comparison — bar chart + table with utilization %, status badges
- [x] 5.2 Top discretionary spending identification — horizontal bar chart of discretionary categories
- [x] 5.3 Subscription audit — table of recurring transactions with estimated annual cost
- [x] 5.4 Category-specific tips — contextual tips for Food, Shopping, Subscriptions, Transport, etc.
- [x] 5.5 "What-if" calculator — interactive calculator showing monthly/annual savings from % reduction
- [x] 5.6 Peer benchmarking — 50/30/20 rule analysis with actual vs ideal comparison chart
- [x] 5.7 Weekly/monthly spending limits — budget progress bars on dashboard with status indicators

## 6. Festive Season Alerts

- [x] 6.1 Festival calendar database — pre-seeded with 8 major festivals from config.yaml
- [x] 6.2 Pre-festival notifications — alert banner with days countdown, historical spend context
- [x] 6.3 Historical festive spending analysis — festive vs normal month comparison chart
- [x] 6.4 Festive savings goal — auto-calculated monthly set-aside recommendation
- [x] 6.5 In-app alert notifications — auto-refreshing alert banner at top of every page (hourly check)
- [x] 6.6 Configurable festival list — add/remove festivals via UI on Festivals page

## 7. ML & Categorization

- [x] 7.1 Model persistence — save/load models with `joblib`; skip retrain if data unchanged (hash check)
- [x] 7.2 Single-class handling — gracefully skips model training when only one class present
- [x] 7.3 Expand keyword dictionaries — 14 expense categories, 6 savings, 6 income with regional terms
- [ ] 7.4 Better feature engineering — add amount ranges, day-of-week as features (future)
- [ ] 7.5 Category taxonomy management — add/edit/merge categories from UI (future)

## 8. Data Import & Export

- [x] 8.1 CSV import with drag-and-drop — upload widget on Import page
- [x] 8.2 Multi-format date parsing — handles YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, etc.
- [x] 8.3 Export to CSV — one-click CSV export of all transactions
- [x] 8.4 Database backup — download DB backup from Settings page
- [ ] 8.5 PDF statement parsing (future — requires `tabula-py` or `pdfplumber`)
- [ ] 8.6 Column mapping UI (future)

## 9. Security & Privacy

- [x] 9.1 Removed committed .db file from repository
- [x] 9.2 Updated .gitignore to exclude DB, logs, saved models, backups
- [ ] 9.3 Database encryption with sqlcipher (future)
- [ ] 9.4 App-level authentication (future)

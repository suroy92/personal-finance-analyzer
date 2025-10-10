import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import re

from keywords import INCOME_KEYWORDS, EXPENSE_KEYWORDS, SAVINGS_KEYWORDS
from database import initialize_database, execute_query
from ml_models import (
    train_models,
    predict_debit_type,
    predict_expense_category,
    predict_savings_category,
)

# -----------------------
# Preprocessing & Heuristics
# -----------------------
def preprocess_description(desc: str) -> str:
    desc = (desc or "").upper()
    # Remove long numeric IDs after hyphens (e.g., ...-110889182110)
    desc = re.sub(r"-\d{6,}", "", desc)
    # Collapse whitespace
    return " ".join(desc.split())

def label_with_keywords(description: str):
    # Try Expense first (most frequent), then Savings, then Income
    for cat, keywords in EXPENSE_KEYWORDS.items():
        if any(k in description for k in keywords):
            return "Expense", cat
    for cat, keywords in SAVINGS_KEYWORDS.items():
        if any(k in description for k in keywords):
            return "Savings/Investment", cat
    for cat, keywords in INCOME_KEYWORDS.items():
        if any(k in description for k in keywords):
            return "Income", cat
    return None, None

# -----------------------
# Small dialogs
# -----------------------
def dropdown_dialog(title: str, prompt: str, options: list, width: int = 420, height: int = 220) -> str | None:
    """Generic dropdown dialog; returns selected option or None."""
    top = tk.Toplevel()
    top.title(title)
    top.geometry(f"{width}x{height}")
    top.grab_set()  # modal

    tk.Label(top, text=prompt, wraplength=width - 30, justify="left").pack(pady=10)

    var = tk.StringVar(top)
    opts = list(dict.fromkeys(options)) or ["(None)"]
    var.set(opts[0])

    tk.OptionMenu(top, var, *opts).pack(pady=10)

    chosen = {"value": None}
    def submit():
        chosen["value"] = var.get()
        top.destroy()

    tk.Button(top, text="Submit", command=submit, width=14).pack(pady=10)
    top.wait_window()
    return chosen["value"]

# -----------------------
# GUI App
# -----------------------
class PersonalFinanceAnalyzer:
    def __init__(self, master):
        self.master = master
        master.title("Personal Finance Analyzer")
        master.geometry("560x470")

        initialize_database()
        self.create_widgets()

        # Train in background once at startup (if there is data)
        threading.Thread(target=train_models, daemon=True).start()

    # -----------------------
    # GUI
    # -----------------------
    def create_widgets(self):
        tk.Label(self.master, text="Welcome to Personal Finance Analyzer!", font=("Arial", 14, "bold")).pack(pady=10)
        btns = tk.Frame(self.master)
        btns.pack(pady=5)

        tk.Button(btns, text="Upload Bank Statement (CSV)", command=self.upload_bank_statement, width=30).grid(row=0, column=0, padx=5, pady=4)
        tk.Button(btns, text="Show Dashboard", command=self.show_dashboard, width=30).grid(row=1, column=0, padx=5, pady=4)
        tk.Button(btns, text="Show Financial Charts", command=self.show_financial_charts, width=30).grid(row=2, column=0, padx=5, pady=4)
        tk.Button(btns, text="Retrain Models Now", command=self.retrain_now, width=30).grid(row=3, column=0, padx=5, pady=4)
        tk.Button(btns, text="Exit", command=self.master.quit, width=30, bg='red', fg='white').grid(row=4, column=0, padx=5, pady=10)

    # -----------------------
    # Manual Category Selection (Dropdown-only with context)
    # -----------------------
    def ask_category_with_dropdown(self, description, amount, category_options, transaction_type_label):
        prompt = f"Description: {description}\nAmount: {amount:,.2f} ({transaction_type_label})\n\nSelect a category:"
        return dropdown_dialog("Categorize Transaction", prompt, category_options)

    def ask_debit_type_dropdown(self, description_raw: str) -> str:
        """Dropdown for choosing whether a DEBIT is Expense or Savings/Investment."""
        options = ["Expense", "Savings/Investment"]
        prompt = f"How should this transaction be treated?\n\n{description_raw}"
        choice = dropdown_dialog("Transaction Type", prompt, options, width=520, height=220)
        return choice or "Expense"

    # -----------------------
    # File Upload & Ingest
    # -----------------------
    def upload_bank_statement(self):
        file_path = filedialog.askopenfilename(
            title="Select Bank Statement CSV",
            filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()

            required_cols = ['Date', 'Narration', 'Debit Amount', 'Credit Amount']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                raise ValueError(f"CSV must contain columns: {required_cols}. Missing: {missing}")

            # Normalize numeric columns
            df['Debit Amount']  = pd.to_numeric(df['Debit Amount'],  errors='coerce').fillna(0.0)
            df['Credit Amount'] = pd.to_numeric(df['Credit Amount'], errors='coerce').fillna(0.0)

            new_training_count = 0

            for _, row in df.iterrows():
                description_raw = str(row['Narration'])
                description = preprocess_description(description_raw)

                amount = 0.0
                transaction_type = None
                category = None
                is_saving = 0

                # CREDIT
                if row['Credit Amount'] > 0:
                    amount = float(row['Credit Amount'])
                    transaction_type = "Credit"

                    # Keyword bootstrap
                    _, category = label_with_keywords(description)

                    # If unknown, ask user from Income categories
                    if not category:
                        category = self.ask_category_with_dropdown(
                            description_raw, amount, list(INCOME_KEYWORDS.keys()), "Credit"
                        )

                    # Persist training example if chosen
                    if category:
                        execute_query(
                            "INSERT INTO training_data (description, category) VALUES (?, ?)",
                            (description, category)
                        )
                        new_training_count += 1

                # DEBIT
                elif row['Debit Amount'] > 0:
                    amount = float(row['Debit Amount'])
                    transaction_type = "Debit"

                    # Keyword bootstrap may return debit_type + category
                    debit_type, category = label_with_keywords(description)

                    # If we couldn’t infer the type with keywords, try ML; if still None, ask user via dropdown
                    if not debit_type:
                        ml_type, ml_conf = predict_debit_type(description)
                        if ml_type and ml_conf > 0.7:
                            debit_type = ml_type
                        else:
                            debit_type = self.ask_debit_type_dropdown(description_raw)

                    if debit_type.lower().startswith("savings"):
                        # Try ML savings category first
                        pred, conf = predict_savings_category(description)
                        if pred and conf > 0.7:
                            category = pred
                        if not category:
                            category = self.ask_category_with_dropdown(
                                description_raw, amount, list(SAVINGS_KEYWORDS.keys()), "Debit"
                            )
                        is_saving = 1
                    else:
                        # Try ML expense category first
                        pred, conf = predict_expense_category(description)
                        if pred and conf > 0.7:
                            category = pred
                        if not category:
                            category = self.ask_category_with_dropdown(
                                description_raw, amount, list(EXPENSE_KEYWORDS.keys()), "Debit"
                            )

                    # Persist training example if chosen
                    if category:
                        execute_query(
                            "INSERT INTO training_data (description, category) VALUES (?, ?)",
                            (description, category)
                        )
                        new_training_count += 1

                else:
                    # neither debit nor credit
                    continue

                # Store transaction itself
                execute_query(
                    """
                    INSERT INTO daily_transactions
                    (date, description, amount, transaction_type, category, is_saving, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row['Date'],
                        description_raw,
                        amount,
                        transaction_type,
                        category,
                        is_saving,
                        datetime.now().isoformat(),
                    ),
                )

            # Retrain in background if we got new training labels
            if new_training_count > 0:
                threading.Thread(target=train_models, daemon=True).start()

            messagebox.showinfo(
                "Success",
                f"Bank statement uploaded successfully!\n{new_training_count} transactions added for training."
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process CSV: {e}")

    # -----------------------
    # Dashboard
    # -----------------------
    def show_dashboard(self):
        rows = execute_query("SELECT * FROM daily_transactions", fetch=True)
        df = pd.DataFrame(
            rows,
            columns=["id", "date", "description", "amount", "transaction_type", "category", "is_saving", "uploaded_at"]
        )
        if df.empty:
            messagebox.showinfo("Dashboard", "No transactions available.")
            return

        total_credit  = df.loc[df['transaction_type'] == "Credit", 'amount'].sum()
        total_debit   = df.loc[df['transaction_type'] == "Debit",  'amount'].sum()
        total_savings = df.loc[df['is_saving'] == 1,              'amount'].sum()

        msg = (
            f"Total Credit: {total_credit:,.2f}\n"
            f"Total Debit: {total_debit:,.2f}\n"
            f"Savings/Investments: {total_savings:,.2f}"
        )
        messagebox.showinfo("Dashboard", msg)

    # -----------------------
    # Financial Charts
    # -----------------------
    def show_financial_charts(self):
        rows = execute_query("SELECT * FROM daily_transactions", fetch=True)
        df = pd.DataFrame(
            rows,
            columns=["id", "date", "description", "amount", "transaction_type", "category", "is_saving", "uploaded_at"]
        )
        if df.empty:
            messagebox.showwarning("No Data", "No transactions to plot.")
            return

        expense_df = df[df['transaction_type'] == "Debit"].groupby('category', dropna=False)['amount'].sum()
        income_df  = df[df['transaction_type'] == "Credit"].groupby('category', dropna=False)['amount'].sum()

        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
        expense_df.sort_values(ascending=False).plot(kind='bar', ax=ax[0], color='red',   title='Expenses by Category')
        income_df.sort_values(ascending=False).plot(kind='bar',  ax=ax[1], color='green', title='Income by Category')
        plt.tight_layout()
        plt.show()

    # -----------------------
    # Retrain Button
    # -----------------------
    def retrain_now(self):
        def _run():
            try:
                train_models()
                messagebox.showinfo("Retrain", "Models retrained successfully.")
            except Exception as e:
                messagebox.showerror("Retrain", f"Failed to retrain models: {e}")

        threading.Thread(target=_run, daemon=True).start()

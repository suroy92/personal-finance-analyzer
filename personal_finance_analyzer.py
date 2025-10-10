import sqlite3
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
import matplotlib.pyplot as plt

console = Console()
DB_FILE = 'expenses.db'

# MAPPING OF KEYWORDS TO CATEGORIES FOR AUTOMATION
CATEGORY_KEYWORDS = {
    'AMAZON': 'Shopping',
    'ZOMATO': 'Food & Dining',
    'BLINKIT': 'Groceries',
    'STARBUCKS': 'Food & Dining',
    'UBER': 'Transportation',
    'NETFLIX': 'Subscriptions',
    'SPOTIFY': 'Subscriptions',
    'ELECTRIC': 'Utilities',
    'WATER': 'Utilities',
    'RENT': 'Housing',
    'DEBIT CARD': 'Shopping',
    'CREDIT CARD': 'Shopping'
}

def initialize_database():
    """Initializes the SQLite database and creates the necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY,
            amount REAL NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recurring_expenses (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL,
            category TEXT,
            next_due_date TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_and_investments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL,
            next_due_date TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_transactions (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            uploaded_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_summary (
            id INTEGER PRIMARY KEY,
            month TEXT NOT NULL UNIQUE,
            total_income REAL NOT NULL,
            total_expenses REAL NOT NULL,
            total_savings_investments REAL NOT NULL
        )
    """)

    # Check if a fixed income is already set
    cursor.execute("SELECT COUNT(*) FROM income")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO income (amount, updated_at) VALUES (?, ?)", (0.0, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def set_fixed_income():
    """Allows the user to set their fixed monthly income."""
    try:
        amount = float(console.input("[bold yellow]Enter your fixed monthly income: [/bold yellow]"))
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE income SET amount = ?, updated_at = ?", (amount, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        console.print(f"[bold green]Income set to ${amount:,.2f}[/bold green]")
    except ValueError:
        console.print("[bold red]Invalid amount. Please enter a number.[/bold red]")

def add_recurring_item():
    """Allows the user to add recurring expenses, savings, or investments."""
    name = console.input("[bold yellow]Enter item name (e.g., Loan, Mutual Fund, Insurance): [/bold yellow]")
    try:
        amount = float(console.input("[bold yellow]Enter amount: [/bold yellow]"))
        frequency = console.input("[bold yellow]Enter frequency (Monthly, Quarterly, Yearly): [/bold yellow]").title()
        item_type = console.input("[bold yellow]Is this an Expense, Saving, or Investment?: [/bold yellow]").lower()
        next_due_date = console.input("[bold yellow]Enter next due date (YYYY-MM-DD): [/bold yellow]")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if item_type == 'expense':
            category = console.input("[bold yellow]Enter expense category (e.g., Insurance, Rent, Utilities): [/bold yellow]")
            cursor.execute("INSERT INTO recurring_expenses (name, amount, frequency, category, next_due_date) VALUES (?, ?, ?, ?, ?)",
                           (name, amount, frequency, category, next_due_date))
        elif item_type in ['saving', 'investment']:
            cursor.execute("INSERT INTO savings_and_investments (name, amount, frequency, next_due_date) VALUES (?, ?, ?, ?)",
                           (name, amount, frequency, next_due_date))
        else:
            console.print("[bold red]Invalid item type. Please enter Expense, Saving, or Investment.[/bold red]")
            return
            
        conn.commit()
        conn.close()
        console.print(f"[bold green]Recurring {item_type} added successfully![/bold green]")
    except ValueError:
        console.print("[bold red]Invalid amount. Please enter a number.[/bold red]")

def upload_bank_statement():
    """Processes a bank statement CSV and records daily transactions, with automated categorization."""
    file_path = console.input("[bold yellow]Enter the path to your bank statement CSV file: [/bold yellow]")
    try:
        df = pd.read_csv(file_path)
        
        if not all(col in df.columns for col in ['Date', 'Description', 'Amount']):
            raise ValueError("CSV must contain 'Date', 'Description', and 'Amount' columns.")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        uncategorized_transactions = df[df['Amount'] < 0]

        if uncategorized_transactions.empty:
            console.print("[bold red]No expense transactions found to categorize.[/bold red]")
            return

        for index, row in uncategorized_transactions.iterrows():
            description = str(row['Description']).upper()
            assigned_category = None
            
            # Automated categorization based on keywords
            for keyword, category in CATEGORY_KEYWORDS.items():
                if keyword in description:
                    assigned_category = category
                    break # Exit the loop once a match is found
            
            # Manual input if no match is found
            if assigned_category is None:
                console.print(f"\n[bold blue]Transaction requires manual categorization:[/bold blue] Description: {row['Description']}, Amount: ${abs(row['Amount']):,.2f}")
                assigned_category = console.input("[bold yellow]Enter category: [/bold yellow]").title()
            else:
                console.print(f"\n[bold green]Automatically categorized:[/bold green] Description: {row['Description']}, [bold magenta]Category: {assigned_category}[/bold magenta]")

            cursor.execute("INSERT INTO daily_transactions (date, description, amount, category, uploaded_at) VALUES (?, ?, ?, ?, ?)",
                           (row['Date'], row['Description'], abs(row['Amount']), assigned_category, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        console.print(f"[bold green]Successfully processed and categorized {len(uncategorized_transactions)} transactions.[/bold green]")
    except FileNotFoundError:
        console.print("[bold red]File not found. Please check the path.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")

def show_dashboard():
    """Displays an overview of income, expenses, and savings."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get fixed income
    income = cursor.execute("SELECT amount FROM income").fetchone()[0]

    # Calculate monthly recurring expenses
    monthly_recurring_expenses = cursor.execute("SELECT SUM(amount) FROM recurring_expenses WHERE frequency = 'Monthly'").fetchone()[0] or 0
    total_daily_expenses = cursor.execute("SELECT SUM(amount) FROM daily_transactions").fetchone()[0] or 0

    # Calculate monthly savings and investments
    monthly_savings_investments = cursor.execute("SELECT SUM(amount) FROM savings_and_investments WHERE frequency = 'Monthly'").fetchone()[0] or 0
    
    # Calculate pro-rated savings for non-monthly items
    quarterly_items = cursor.execute("SELECT SUM(amount) FROM savings_and_investments WHERE frequency = 'Quarterly'").fetchone()[0] or 0
    yearly_items = cursor.execute("SELECT SUM(amount) FROM savings_and_investments WHERE frequency = 'Yearly'").fetchone()[0] or 0
    
    total_savings_investments = monthly_savings_investments + (quarterly_items / 3) + (yearly_items / 12)

    conn.close()

    console.print("\n" + "*"*50, style="bold blue")
    console.print("  PERSONAL EXPENSE TRACKER DASHBOARD", style="bold yellow")
    console.print("*"*50 + "\n", style="bold blue")

    table = Table(title="Monthly Financial Summary")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Amount", style="green")

    table.add_row("Total Monthly Income", f"${income:,.2f}")
    table.add_row("Fixed Monthly Expenses", f"${monthly_recurring_expenses:,.2f}")
    table.add_row("Total Daily Expenses", f"${total_daily_expenses:,.2f}")
    table.add_row("Total Monthly Savings & Investments", f"${total_savings_investments:,.2f}")
    
    remaining_income = income - monthly_recurring_expenses - total_daily_expenses - total_savings_investments
    table.add_row("Remaining Income", f"${remaining_income:,.2f}", style="bold magenta")
    
    console.print(table)

def show_pie_chart():
    """Generates and displays a pie chart of income, expenses, and savings."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    income = cursor.execute("SELECT amount FROM income").fetchone()[0]
    total_recurring_expenses = cursor.execute("SELECT SUM(amount) FROM recurring_expenses").fetchone()[0] or 0
    total_daily_expenses = cursor.execute("SELECT SUM(amount) FROM daily_transactions").fetchone()[0] or 0
    total_savings_investments = cursor.execute("SELECT SUM(amount) FROM savings_and_investments").fetchone()[0] or 0

    conn.close()

    total_expenses = total_recurring_expenses + total_daily_expenses
    remaining_income = max(0, income - total_expenses - total_savings_investments)

    labels = ['Total Expenses', 'Total Savings & Investments', 'Remaining Income']
    sizes = [total_expenses, total_savings_investments, remaining_income]
    colors = ['#ff9999','#66b3ff','#99ff99']
    
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12, 'fontweight': 'bold'})
    ax1.axis('equal')  
    
    plt.title('Income Allocation Breakdown', fontsize=16, fontweight='bold')
    plt.show()

def show_analytics():
    """Generates and displays a line chart of expenses and savings trends over time."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT month, total_expenses, total_savings_investments FROM monthly_summary ORDER BY month")
    data = cursor.fetchall()
    conn.close()

    if not data:
        console.print("[bold red]No historical data available to generate charts. Run the 'Update Monthly Summary' command first.[/bold red]")
        return

    months = [row[0] for row in data]
    expenses = [row[1] for row in data]
    savings = [row[2] for row in data]

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(months, expenses, label='Expenses', marker='o', color='red')
    plt.plot(months, savings, label='Savings & Investments', marker='o', color='green')

    plt.title('Expenses vs. Savings & Investments Trend', fontsize=16, fontweight='bold')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def update_monthly_summary():
    """Calculates and stores a summary of the current month's finances."""
    month_key = datetime.now().strftime('%Y-%m')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Calculate totals for the current month
    income = cursor.execute("SELECT amount FROM income").fetchone()[0] or 0
    total_recurring_expenses = cursor.execute("SELECT SUM(amount) FROM recurring_expenses").fetchone()[0] or 0
    total_daily_expenses = cursor.execute("SELECT SUM(amount) FROM daily_transactions WHERE date LIKE ?", (f'{month_key}%',)).fetchone()[0] or 0
    total_savings_investments = cursor.execute("SELECT SUM(amount) FROM savings_and_investments").fetchone()[0] or 0

    total_expenses = total_recurring_expenses + total_daily_expenses

    try:
        cursor.execute("INSERT INTO monthly_summary (month, total_income, total_expenses, total_savings_investments) VALUES (?, ?, ?, ?)",
                       (month_key, income, total_expenses, total_savings_investments))
        conn.commit()
        console.print(f"[bold green]Monthly summary for {month_key} updated successfully.[/bold green]")
    except sqlite3.IntegrityError:
        console.print(f"[bold red]Summary for {month_key} already exists. Skipping update.[/bold red]")
    finally:
        conn.close()


def main_menu():
    """Main application loop."""
    initialize_database()
    
    markdown = Markdown("""
    # Welcome to your Expense Tracker!

    **Commands:**
    1. **Set Income**
    2. **Add Recurring Item (Expense, Savings, Investment)**
    3. **Upload Bank Statement (CSV)**
    4. **Show Dashboard**
    5. **Show Pie Chart**
    6. **Show Analytics (Trends)**
    7. **Update Monthly Summary (for analytics)**
    8. **Exit**
    """)
    
    while True:
        console.print(markdown)
        choice = console.input("[bold magenta]Enter your choice (1-8): [/bold magenta]")
        
        if choice == '1':
            set_fixed_income()
        elif choice == '2':
            add_recurring_item()
        elif choice == '3':
            upload_bank_statement()
        elif choice == '4':
            show_dashboard()
        elif choice == '5':
            show_pie_chart()
        elif choice == '6':
            show_analytics()
        elif choice == '7':
            update_monthly_summary()
        elif choice == '8':
            console.print("[bold]Exiting. Goodbye! 👋[/bold]")
            break
        else:
            console.print("[bold red]Invalid choice. Please enter a number from 1 to 8.[/bold red]")

if __name__ == "__main__":
    main_menu()
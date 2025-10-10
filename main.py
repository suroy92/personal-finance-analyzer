import tkinter as tk
from app import PersonalFinanceAnalyzer

def main():
    root = tk.Tk()
    app = PersonalFinanceAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()

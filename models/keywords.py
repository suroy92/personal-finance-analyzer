INCOME_KEYWORDS = {
    "Salary": ["SALARY", "CONSULTANCY CHARGES", "A2AINT01", "PAYROLL", "HR DEPT", "WAGE"],
    "Refund": ["REV-UPI", "REFUND", "REVERSAL"],
    "Interest": ["INTEREST", "DIVIDEND", "INT PAID"],
    "Transfer In": ["NEFT", "IMPS", "UPI CREDIT", "CASHBACK", "REWARD", "RTGS"],
    "Freelance": ["FREELANCE", "CONSULTING", "CONTRACT"],
    "Rental Income": ["RENT RECEIVED", "TENANT", "LEASE"],
}

EXPENSE_KEYWORDS = {
    "Food & Dining": [
        "ZOMATO", "SWIGGY", "STARBUCKS", "HAVE A BREAK", "CAFE", "RESTAURANT",
        "DOMINOS", "PIZZA", "MCDONALD", "KFC", "DUNKIN", "BURGER",
    ],
    "Groceries": [
        "BLINKIT", "GROFERS", "SUPERMARKET", "BIGBASKET", "JIOMART",
        "DMART", "RELIANCE FRESH", "SPENCER", "MORE RETAIL",
    ],
    "Transportation": [
        "UBER", "OLA", "UBERRIDE", "TAXI", "METRO", "RAPIDO",
        "IRCTC", "RAILWAY", "REDBUS", "BUS TICKET",
    ],
    "Shopping": [
        "TANISHQ", "FASHNEAR", "MEESHO", "AMAZON", "PAYTM MALL",
        "FLIPKART", "MYNTRA", "AJIO", "NYKAA", "TATA CLIQ",
    ],
    "Subscriptions": [
        "APPLE SERVICES", "APPLE MEDIA SERVICES", "NETFLIX", "SPOTIFY", "PRIME",
        "HOTSTAR", "YOUTUBE PREMIUM", "JIOCINEMA", "DISNEY",
    ],
    "Utilities": [
        "CESC LIMITED", "ELECTRIC", "WATER", "UTILITY", "BILL",
        "BROADBAND", "WIFI", "INTERNET", "GAS BILL", "PHONE BILL",
    ],
    "Fuel": ["FUEL ST", "PETROL", "GAS STATION", "DIESEL", "IOCL", "BPCL", "HPCL"],
    "Healthcare": [
        "HOSPITAL", "PHARMACY", "MEDICAL", "DOCTOR", "CLINIC",
        "APOLLO", "MEDPLUS", "1MG", "PHARMEASY", "NETMEDS",
    ],
    "Education": [
        "SCHOOL", "COLLEGE", "TUITION", "COURSE", "UDEMY",
        "COURSERA", "UNACADEMY", "BYJU",
    ],
    "Rent": ["RENT", "HOUSING", "PG CHARGES", "HOSTEL"],
    "Entertainment": [
        "MOVIE", "BOOKMYSHOW", "PVR", "INOX", "GAMING",
        "STEAM", "PLAYSTATION",
    ],
    "Travel": [
        "MAKEMYTRIP", "GOIBIBO", "CLEARTRIP", "HOTEL", "AIRBNB",
        "OYO", "AIRLINE", "FLIGHT", "INDIGO", "AIRINDIA",
    ],
    "Personal Care": ["SALON", "SPA", "PARLOUR", "GROOMING", "URBANCLAP"],
}

SAVINGS_KEYWORDS = {
    "Mutual Fund SIP": ["INVESTNOWIP", "SIP", "MUTUAL FUND", "MF PURCHASE"],
    "Insurance": ["BAJAJ ALLIANZ LIFE", "LIC", "INSURANCE", "HDFC LIFE", "ICICI PRUDENTIAL"],
    "Fixed Deposit": ["FD", "FIXED DEPOSIT", "RD", "RECURRING DEPOSIT"],
    "Retirement": ["EPF", "PPF", "NPS", "RETIREMENT", "PENSION"],
    "Stocks": ["ZERODHA", "GROWW", "UPSTOX", "SHARE PURCHASE", "EQUITY"],
    "Gold": ["GOLD", "SOVEREIGN GOLD BOND", "SGB", "DIGITAL GOLD"],
}

# Categories grouped by type for UI dropdowns
ALL_EXPENSE_CATEGORIES = list(EXPENSE_KEYWORDS.keys())
ALL_SAVINGS_CATEGORIES = list(SAVINGS_KEYWORDS.keys())
ALL_INCOME_CATEGORIES = list(INCOME_KEYWORDS.keys())

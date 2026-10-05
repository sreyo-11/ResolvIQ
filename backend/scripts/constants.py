CATEGORIES = ["billing", "account", "technical", "shipping", "integrations", "general"]
PRIORITIES = ["low", "medium", "high", "urgent"]

CATEGORY_TEAM = {
    "billing": "Billing Support",
    "account": "Account Security",
    "technical": "Tech Support",
    "shipping": "Logistics",
    "integrations": "Integrations",
    "general": "General Support",
}

SLA_MINUTES = {"urgent": 60, "high": 240, "medium": 480, "low": 1440}  # first-response limits

AGENTS = [
    ("Aarav Sharma", "Billing Support"), ("Meera Iyer", "Billing Support"),
    ("Rohan Verma", "Account Security"), ("Ishita Rao", "Account Security"),
    ("Kabir Singh", "Tech Support"), ("Ananya Das", "Tech Support"),
    ("Vihaan Gupta", "Tech Support"), ("Diya Nair", "Logistics"),
    ("Arjun Mehta", "Logistics"), ("Sana Khan", "Integrations"),
    ("Neil Fernandes", "Integrations"), ("Tara Joshi", "General Support"),
]
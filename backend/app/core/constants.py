CATEGORIES = ["billing", "account", "technical", "shipping", "integrations", "general"]
PRIORITIES = ["low", "medium", "high", "urgent"]  # index = severity rank

CATEGORY_TEAM = {
    "billing": "Billing Support",
    "account": "Account Security",
    "technical": "Tech Support",
    "shipping": "Logistics",
    "integrations": "Integrations",
    "general": "General Support",
}
TRIAGE_TEAM = "General Support"  # where low-confidence tickets wait for a human

SLA_MINUTES = {"urgent": 60, "high": 240, "medium": 480, "low": 1440}  # first-response limits
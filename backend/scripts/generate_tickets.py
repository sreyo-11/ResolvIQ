"""Generate a synthetic support-ticket dataset -> data/tickets_synthetic.csv

Usage (from backend/):  python -m scripts.generate_tickets --n 1500
"""
import argparse
import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.constants import AGENTS, CATEGORIES, CATEGORY_TEAM, PRIORITIES, SLA_MINUTES

OUT = Path(__file__).resolve().parents[2] / "data" / "tickets_synthetic.csv"

CATEGORY_WEIGHTS = [0.24, 0.18, 0.22, 0.14, 0.12, 0.10]
PRIORITY_WEIGHTS = [0.28, 0.45, 0.20, 0.07]
PRIORITY_WEIGHTS_TECH = [0.15, 0.40, 0.30, 0.15]
RESPONSE_RATIO = {"urgent": 0.45, "high": 0.38, "medium": 0.32, "low": 0.25}

SUBJECTS = {
    "billing": ["Charged twice for my subscription", "Refund for cancelled plan",
                "Invoice shows wrong amount", "Card declined but money deducted",
                "Need GST invoice for last month", "Unexpected charge on my account"],
    "account": ["Can't log in to my account", "Password reset email never arrives",
                "Two-factor codes not working", "Account locked after failed attempts",
                "Unknown login from another country", "Delete my account and data"],
    "technical": ["App crashes when exporting report", "Dashboard stuck on loading spinner",
                  "Getting error 500 on upload", "Slow performance since last update",
                  "Files not syncing across devices", "Mobile app freezes on startup"],
    "shipping": ["Order still not delivered", "Package marked delivered but missing",
                 "Wrong item received", "Tracking link shows no updates",
                 "Need to change delivery address", "Damaged product on arrival"],
    "integrations": ["Slack integration stopped posting", "Webhook deliveries failing",
                     "API key returns 401 unauthorized", "Zapier connection keeps disconnecting",
                     "Salesforce sync duplicates contacts", "Rate limit errors on API"],
    "general": ["Question about enterprise pricing", "Do you offer student discounts",
                "Feature request: dark mode", "Need a product demo",
                "Looking for a data processing agreement", "Feedback on the new interface"],
}

ISSUES = {
    "billing": [
        "I was charged {amount} twice for my {plan} plan this month.",
        "I cancelled my {plan} subscription last week and have not received the refund.",
        "The invoice for {plan} shows {amount} but I expected a lower amount.",
        "My card was declined at checkout but {amount} still left my bank account.",
        "I need a GST invoice for my {plan} subscription for our accounting.",
        "There is a charge of {amount} on my statement that I do not recognise.",
    ],
    "account": [
        "I cannot log in even though I am sure my password is correct.",
        "I requested a password reset three times but no email has arrived.",
        "My authenticator codes are rejected every time I try to sign in.",
        "My account got locked after a few failed logins and I cannot get back in.",
        "I got an alert about a login from a country I have never visited.",
        "Please delete my account and all my personal data permanently.",
    ],
    "technical": [
        "The app crashes every time I try to export a report to CSV.",
        "The dashboard never finishes loading, it just shows the spinner forever.",
        "Uploading any file fails with an error 500 message.",
        "Everything has become very slow since the last update, pages take ages to open.",
        "My files are not syncing between my laptop and my phone anymore.",
        "The mobile app freezes on the splash screen right after launch.",
    ],
    "shipping": [
        "My order {order} was supposed to arrive last week and still has not been delivered.",
        "Tracking says order {order} was delivered but nothing is at my door.",
        "I received the wrong item in order {order}, this is not what I ordered.",
        "The tracking link for order {order} has not shown any update for days.",
        "I entered the wrong address for order {order} and need to change it.",
        "The product from order {order} arrived with a broken screen.",
    ],
    "integrations": [
        "Our Slack integration stopped posting notifications to the channel.",
        "Webhook deliveries to our endpoint keep failing and events are missing.",
        "Our API key returns 401 unauthorized on every request since this morning.",
        "The Zapier connection keeps disconnecting and needs re-authorising daily.",
        "The Salesforce sync keeps creating duplicate contacts in our CRM.",
        "We are hitting 429 rate limit errors on the API even with low traffic.",
    ],
    "general": [
        "Could you share pricing details for the enterprise plan for about 200 seats?",
        "Do you offer any discount for students or non-profit organisations?",
        "It would be great to have a dark mode option in the app.",
        "We would like to schedule a product demo for our team.",
        "Can you send us your standard data processing agreement?",
        "I wanted to share some feedback about the new interface layout.",
    ],
}

PRIORITY_PHRASES = {
    "urgent": ["This is blocking our entire team in production.",
               "We are losing customers every minute, need help ASAP!",
               "Critical: our live system is affected."],
    "high": ["This is affecting several of our users.", "Need this fixed today please.",
             "Quite urgent for us, deadline is tomorrow."],
    "medium": ["Would appreciate help this week.", "It is annoying but we can work around it."],
    "low": ["No rush at all.", "Just whenever you get time.", "Not urgent, low priority for me."],
}

OPENERS = ["Hi team,", "Hello,", "Hi,", "Good morning,", ""]
DETAILS = ["This started yesterday.", "I already tried restarting everything.",
           "Using version {app_version} on {device}.", "Happy to share screenshots if needed.",
           "This has happened more than once now."]
CLOSERS = ["Please help.", "Thanks in advance.", "Regards, {name}", "Thanks, {name}", ""]
VAGUE_SUBJECTS = ["help", "issue", "urgent!!", "need assistance", "question", "problem"]
VAGUE_BODIES = ["it is not working please check", "something is wrong with my account",
                "can someone look into this", "I need help with this as soon as possible"]
PLANS = ["Pro", "Business", "Starter", "Team"]
DEVICES = ["Windows 11", "macOS", "Android", "iPhone", "Ubuntu"]
FIRST = ["Aditya", "Priya", "Rahul", "Sneha", "Karan", "Neha", "Vikram", "Pooja", "Amit", "Riya"]
LAST = ["Patel", "Kumar", "Singh", "Reddy", "Mishra", "Jain", "Bose", "Kapoor", "Yadav", "Shah"]

SPIKE_SUBJECTS = ["Webhook deliveries failing with 502", "Webhooks stopped firing after v4.2 update",
                  "502 Bad Gateway on webhook endpoint", "Events not reaching our server since update",
                  "Webhook retries exhausted, 502 errors"]
SPIKE_BODIES = [
    "Since the v4.2.0 update our webhook endpoint receives 502 Bad Gateway and no events arrive.",
    "None of our webhooks have fired since yesterday's release. The delivery log shows 502.",
    "We upgraded to v4.2.0 and all webhook deliveries now fail with 502. Retries are exhausted.",
    "Our integration depends on webhooks and they return 502 errors since the latest update.",
]


def add_typos(text: str, rng: random.Random, rate: float = 0.05) -> str:
    words = text.split()
    for i, w in enumerate(words):
        if len(w) > 4 and rng.random() < rate:
            j = rng.randrange(1, len(w) - 2)
            words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def compose(rng: random.Random, category: str, priority: str) -> tuple[str, str, str]:
    i = rng.randrange(len(SUBJECTS[category]))
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    ctx = {
        "order": f"#{rng.randint(100000, 999999)}", "plan": rng.choice(PLANS),
        "amount": f"${rng.choice([9, 19, 29, 49, 99, 199])}",
        "app_version": f"{rng.randint(3, 4)}.{rng.randint(0, 9)}.{rng.randint(0, 3)}",
        "device": rng.choice(DEVICES), "name": name.split()[0],
    }
    parts = [rng.choice(OPENERS), ISSUES[category][i]]
    parts += rng.sample(DETAILS, k=rng.randint(0, 2))
    parts += [rng.choice(PRIORITY_PHRASES[priority]), rng.choice(CLOSERS)]
    body = " ".join(p.format(**ctx) for p in parts if p)
    email = f"{name.lower().replace(' ', '.')}{rng.randint(1, 99)}@example.com"
    return SUBJECTS[category][i], body, email


def random_created(rng: random.Random, now: datetime, days: int) -> datetime:
    t = now - timedelta(minutes=rng.random() * days * 1440)
    if rng.random() < 0.7:  # most tickets arrive in business hours
        t = t.replace(hour=rng.randint(9, 17), minute=rng.randint(0, 59))
    return min(t, now - timedelta(minutes=1))


def response_minutes(rng, priority, created, queue_len, agent_load) -> float:
    median = RESPONSE_RATIO[priority] * SLA_MINUTES[priority]
    factor = (1 + 0.04 * queue_len) * (1 + 0.03 * agent_load)
    if created.weekday() >= 5:
        factor *= 1.4
    if not 9 <= created.hour < 18:
        factor *= 1.25
    return median * factor * rng.lognormvariate(0, 0.7)


def finalize(rng, now, agents_by_team, *, created, category, priority, subject, body, email,
             surge=False) -> dict:
    team = CATEGORY_TEAM[category]
    queue = max(0, int(rng.gauss(10 if 9 <= created.hour < 18 else 5, 3))) + (10 if surge else 0)
    load = min(12, max(0, int(rng.gauss(4, 2)))) + (3 if surge else 0)
    resp_min = response_minutes(rng, priority, created, queue, load)
    first_response = created + timedelta(minutes=resp_min)
    resolved = first_response + timedelta(minutes=rng.lognormvariate(math.log(240), 0.9))
    if first_response > now:
        first_response = resolved = None
    elif resolved > now:
        resolved = None

    if resolved:
        status = rng.choices(["resolved", "closed"], weights=[0.3, 0.7])[0]
    elif first_response:
        status = "in_progress"
    else:
        status = rng.choice(["new", "classified", "assigned"])
    has_agent = status in ("assigned", "in_progress", "resolved", "closed")
    iso = lambda d: d.isoformat() if d else ""  # noqa: E731
    return {
        "subject": subject, "body": body, "customer_email": email, "status": status,
        "category": category, "priority": priority, "team": team,
        "agent_name": rng.choice(agents_by_team[team]) if has_agent else "",
        "queue_length_at_creation": queue,
        "agent_load_at_assignment": load if has_agent else "",
        "reopen_count": 1 if resolved and rng.random() < 0.06 else 0,
        "created_at": iso(created), "first_response_at": iso(first_response),
        "resolved_at": iso(resolved),
    }


def generate(n: int, days: int, spike: int, seed: int, label_noise: float) -> list[dict]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    agents_by_team: dict[str, list[str]] = {}
    for name, team in AGENTS:
        agents_by_team.setdefault(team, []).append(name)

    rows, history = [], []
    for _ in range(n):
        if history and rng.random() < 0.03:  # duplicate tickets from the same customer
            subject, body, email, category, priority = rng.choice(history)
        else:
            category = rng.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]
            weights = PRIORITY_WEIGHTS_TECH if category in ("technical", "integrations") \
                else PRIORITY_WEIGHTS
            priority = rng.choices(PRIORITIES, weights=weights)[0]
            subject, body, email = compose(rng, category, priority)
            if rng.random() < 0.12:
                body = add_typos(body, rng)
            if rng.random() < 0.08:
                subject, body = subject.lower(), body.lower()
            if rng.random() < 0.07:
                subject = rng.choice(VAGUE_SUBJECTS)
            if rng.random() < 0.04:
                body = rng.choice(VAGUE_BODIES)
            history.append((subject, body, email, category, priority))
        label = category
        if rng.random() < label_noise:  # historical mis-routing
            label = rng.choice([c for c in CATEGORIES if c != category])
        rows.append(finalize(rng, now, agents_by_team, created=random_created(rng, now, days),
                             category=label, priority=priority, subject=subject, body=body,
                             email=email))

    for _ in range(spike):  # incident: webhook 502s after release v4.2.0
        created = now - timedelta(hours=72 * rng.random() ** 1.6)
        created = min(created, now - timedelta(minutes=1))
        priority = rng.choices(["medium", "high", "urgent"], weights=[0.2, 0.5, 0.3])[0]
        body = add_typos(rng.choice(SPIKE_BODIES) + " " + rng.choice(PRIORITY_PHRASES[priority]),
                         rng, 0.03)
        email = f"{rng.choice(FIRST).lower()}.{rng.choice(LAST).lower()}{rng.randint(1, 999)}@example.com"
        rows.append(finalize(rng, now, agents_by_team, created=created, category="integrations",
                             priority=priority, subject=rng.choice(SPIKE_SUBJECTS), body=body,
                             email=email, surge=True))
    rows.sort(key=lambda r: r["created_at"])
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1500)
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--spike", type=int, default=70)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--label-noise", type=float, default=0.03)
    args = ap.parse_args()

    rows = generate(args.n, args.days, args.spike, args.seed, args.label_noise)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    responded = [r for r in rows if r["first_response_at"]]
    breached = sum(
        1 for r in responded
        if (datetime.fromisoformat(r["first_response_at"]) - datetime.fromisoformat(r["created_at"]))
        .total_seconds() / 60 > SLA_MINUTES[r["priority"]]
    )
    print(f"Wrote {len(rows)} tickets to {OUT}")
    print(f"SLA breach rate among responded tickets: {breached / len(responded):.1%}")


if __name__ == "__main__":
    main()
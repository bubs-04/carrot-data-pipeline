"""
generate_data.py

Creates FAKE partner files that mimic what a fertility-benefits company might
receive from employers and claims partners. Everything here is made up.
The data is deliberately messy, because real partner data always is.

Run it from your project folder:
    python generate_data.py

Output (created next to this script):
    landing/eligibility/eligibility_<employer>_<date>.csv   (5 employers x 3 days)
    landing/claims/claims_<date>.csv                        (3 days)
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

# Fixed seed = the "random" data is identical every time you run this.
# Reproducibility matters in data work: you can re-run and get the same result.
random.seed(42)

LANDING = Path("landing")

EMPLOYERS = {
    "EMP001": "Acme Robotics",
    "EMP002": "Northwind Foods",
    "EMP003": "Globex Logistics",
    "EMP004": "Initech Software",
    "EMP005": "Umbrella Retail",
}

FIRST_NAMES = ["Ava", "Liam", "Noah", "Maya", "Ethan", "Sofia", "Lucas", "Zara",
               "Mia", "Omar", "Priya", "Jonas", "Elena", "Diego", "Hana", "Ravi"]
LAST_NAMES = ["Smith", "Garcia", "Chen", "Patel", "Muller", "Okafor", "Rossi",
              "Kim", "Silva", "Novak", "Haddad", "Larsen", "Reyes", "Tanaka"]

# One real country code -> several ways a partner might spell it (messy!)
COUNTRIES = {
    "US": ["US", "USA", "United States"],
    "GB": ["GB", "UK", "United Kingdom"],
    "CA": ["CA", "Canada"],
    "DE": ["DE", "Germany"],
    "IN": ["IN", "India"],
}

# service_type -> (min_amount, max_amount) in USD
SERVICES = {
    "consultation": (150, 400),
    "ivf_cycle": (8000, 20000),
    "egg_freezing": (6000, 12000),
    "fertility_medication": (300, 4000),
    "pregnancy_coaching": (50, 200),
    "menopause_care": (100, 500),
}
SERVICE_WEIGHTS = [40, 8, 8, 20, 14, 10]  # consultations are most common

# Three daily "drops", like a nightly file arriving from each partner
DAYS = [date(2026, 11, 13), date(2026, 11, 14), date(2026, 11, 15)]

ELIGIBILITY_COLUMNS = [
    "member_id", "employer_id", "first_name", "last_name", "date_of_birth",
    "email", "country", "coverage_start", "coverage_end", "status",
]
CLAIMS_COLUMNS = [
    "claim_id", "member_id", "service_date", "service_type",
    "amount_usd", "claim_status", "submitted_at",
]


# ---------------------------------------------------------------- members
def make_member(counter, employer_id, coverage_start):
    """Build one clean fake member (a dict). Messiness is added later."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    birth = date(1965, 1, 1) + timedelta(days=random.randint(0, 365 * 35))
    return {
        "member_id": f"M{counter:06d}",
        "employer_id": employer_id,
        "first_name": first,
        "last_name": last,
        "date_of_birth": birth.isoformat(),
        "email": f"{first}.{last}{counter}@example.com".lower(),
        "country_code": random.choice(list(COUNTRIES)),
        "coverage_start": coverage_start.isoformat(),
        "coverage_end": "",
        "status": "active",
    }


def messy_eligibility_row(member):
    """Copy a clean member and corrupt it the way real partner files are corrupted."""
    row = dict(member)  # copy, so the real member record stays clean
    row["country"] = random.choice(COUNTRIES[row.pop("country_code")])
    if random.random() < 0.03:
        row["email"] = ""  # missing email
    if random.random() < 0.01:
        year, month, day = row["date_of_birth"].split("-")
        row["date_of_birth"] = f"{month}/{day}/{year}"  # different date format
    return row


def write_eligibility(employer_id, members, day):
    rows = [messy_eligibility_row(m) for m in members if m["employer_id"] == employer_id]
    rows += random.sample(rows, k=max(1, len(rows) // 50))  # partner sent some rows twice
    path = LANDING / "eligibility" / f"eligibility_{employer_id}_{day.isoformat()}.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ELIGIBILITY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# ----------------------------------------------------------------- claims
def write_claims(day, members, claim_counter, previous_rows):
    active = [m for m in members if m["status"] == "active"]
    rows = []
    for _ in range(300):
        member = random.choice(active)
        service = random.choices(list(SERVICES), weights=SERVICE_WEIGHTS)[0]
        low, high = SERVICES[service]
        service_date = day - timedelta(days=random.randint(0, 30))
        amount = round(random.uniform(low, high), 2)
        member_id = member["member_id"]

        # --- deliberately planted problems ---
        if random.random() < 0.01:
            amount = -amount            # negative amount
        if random.random() < 0.01:
            amount = ""                 # missing amount
        if random.random() < 0.01:
            member_id = "M999999"       # member that doesn't exist
        if random.random() < 0.01:
            service_date = day + timedelta(days=30)  # service date in the future

        rows.append({
            "claim_id": f"CLM{claim_counter:07d}",
            "member_id": member_id,
            "service_date": service_date.isoformat(),
            "service_type": service,
            "amount_usd": amount,
            "claim_status": random.choices(
                ["approved", "submitted", "denied"], weights=[70, 20, 10])[0],
            "submitted_at": f"{day.isoformat()}T{random.randint(0, 23):02d}:"
                            f"{random.randint(0, 59):02d}:00",
        })
        claim_counter += 1

    # Partner re-sends a few of yesterday's claims (duplicates across days)
    if previous_rows:
        rows += random.sample(previous_rows, k=max(1, len(previous_rows) // 50))

    path = LANDING / "claims" / f"claims_{day.isoformat()}.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CLAIMS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows, claim_counter


# ------------------------------------------------------------------- main
def main():
    (LANDING / "eligibility").mkdir(parents=True, exist_ok=True)
    (LANDING / "claims").mkdir(parents=True, exist_ok=True)

    # Starting population: 200 members per employer, covered since Jan 1
    members = []
    counter = 1
    for employer_id in EMPLOYERS:
        for _ in range(200):
            members.append(make_member(counter, employer_id, date(2026, 1, 1)))
            counter += 1

    claim_counter = 1
    previous_claims = []

    for i, day in enumerate(DAYS):
        if i > 0:
            # Some members leave coverage...
            active = [m for m in members if m["status"] == "active"]
            for m in random.sample(active, 15):
                m["status"] = "terminated"
                m["coverage_end"] = day.isoformat()
            # ...and some new members join
            for employer_id in EMPLOYERS:
                for _ in range(5):
                    members.append(make_member(counter, employer_id, day))
                    counter += 1

        total_elig = sum(write_eligibility(e, members, day) for e in EMPLOYERS)
        previous_claims, claim_counter = write_claims(
            day, members, claim_counter, previous_claims)
        print(f"{day}: {total_elig} eligibility rows, {len(previous_claims)} claim rows")

    print("\nDone. Look inside the landing/ folder.")


if __name__ == "__main__":
    main()

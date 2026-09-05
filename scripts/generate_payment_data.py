#!/usr/bin/env python3
"""
Synthetic Payment Data Generator

Generates realistic but clearly synthetic payment transaction data
with controlled fraud scenarios. This supplements the Kaggle creditcard.csv
dataset with proper payment fields (customer_id, merchant_id, device_id, etc.)
that the original PCA-transformed dataset lacks.

All generated data is SYNTHETIC and clearly documented as such.
"""
import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict

# Seed for reproducibility
random.seed(42)

# ── Constants ────────────────────────────────────────────────────────────────
NUM_CUSTOMERS = 500
NUM_MERCHANTS = 100
NUM_DEVICES = 300
NUM_TRANSACTIONS = 5000
FRAUD_RATE = 0.03  # 3% fraud rate for synthetic data (higher than real for demo)

COUNTRIES = ["US", "US", "US", "US", "UK", "UK", "CA", "DE", "FR", "BR", "NG", "RU", "CN"]
PAYMENT_METHODS = ["credit_card", "debit_card", "digital_wallet", "bank_transfer"]
CARD_TYPES = ["visa", "mastercard", "amex", "discover"]
CHANNELS = ["online", "online", "online", "in_store", "mobile", "phone"]
MERCHANT_CATEGORIES = [
    "retail", "grocery", "restaurant", "gas_station", "electronics",
    "travel", "entertainment", "healthcare", "education", "financial_services",
    "jewelry", "gaming", "crypto_exchange",
]

# Fraud scenario configurations
FRAUD_SCENARIOS = {
    "HIGH_AMOUNT_ANOMALY": {"weight": 0.20, "description": "Unusually high transaction amount"},
    "VELOCITY_ATTACK": {"weight": 0.20, "description": "Burst of rapid transactions"},
    "NEW_DEVICE_ATTACK": {"weight": 0.15, "description": "New device with high-value transaction"},
    "IMPOSSIBLE_TRAVEL": {"weight": 0.10, "description": "Transactions from distant locations in short time"},
    "MERCHANT_ABUSE": {"weight": 0.10, "description": "Suspicious merchant patterns"},
    "CARD_TESTING": {"weight": 0.15, "description": "Small rapid transactions to test stolen cards"},
    "BURST_TRANSACTIONS": {"weight": 0.10, "description": "Multiple transactions in seconds"},
}


def generate_customers(n: int) -> List[Dict]:
    """Generate synthetic customer profiles."""
    customers = []
    for i in range(n):
        customer = {
            "customer_id": f"CUST-{uuid.uuid4().hex[:8].upper()}",
            "country": random.choice(["US", "US", "US", "UK", "CA"]),
            "account_age_days": random.randint(30, 3650),
            "avg_transaction_amount": random.uniform(20, 500),
            "historical_transaction_count": random.randint(10, 5000),
        }
        customers.append(customer)
    return customers


def generate_merchants(n: int) -> List[Dict]:
    """Generate synthetic merchant profiles."""
    merchants = []
    for i in range(n):
        merchant = {
            "merchant_id": f"MERCH-{uuid.uuid4().hex[:8].upper()}",
            "category": random.choice(MERCHANT_CATEGORIES),
            "country": random.choice(COUNTRIES),
            "avg_transaction_amount": random.uniform(10, 1000),
            "risk_tier": random.choices(["low", "medium", "high"], weights=[0.7, 0.2, 0.1])[0],
        }
        merchants.append(merchant)
    return merchants


def generate_devices(n: int) -> List[str]:
    """Generate synthetic device IDs."""
    return [f"DEV-{uuid.uuid4().hex[:12].upper()}" for _ in range(n)]


def generate_legitimate_transaction(
    customer: Dict, merchant: Dict, devices: List[str], base_time: datetime
) -> Dict:
    """Generate a legitimate transaction."""
    amount = max(0.50, random.gauss(customer["avg_transaction_amount"], customer["avg_transaction_amount"] * 0.5))
    return {
        "transaction_id": f"TXN-{uuid.uuid4().hex[:12].upper()}",
        "customer_id": customer["customer_id"],
        "merchant_id": merchant["merchant_id"],
        "amount": round(amount, 2),
        "currency": "USD",
        "timestamp": (base_time + timedelta(seconds=random.randint(0, 86400))).isoformat(),
        "payment_method": random.choice(PAYMENT_METHODS),
        "card_type": random.choice(CARD_TYPES),
        "device_id": random.choice(devices[:5]),  # Customers use few devices
        "ip_address": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
        "country": customer["country"],
        "merchant_category": merchant["category"],
        "channel": random.choice(CHANNELS),
        "is_fraud": 0,
        "fraud_scenario": None,
    }


def generate_fraud_transaction(
    customer: Dict, merchant: Dict, devices: List[str], base_time: datetime, scenario: str
) -> List[Dict]:
    """Generate fraudulent transaction(s) for a given scenario."""
    transactions = []
    ts = base_time + timedelta(seconds=random.randint(0, 86400))

    if scenario == "HIGH_AMOUNT_ANOMALY":
        amount = random.uniform(5000, 50000)
        txn = generate_legitimate_transaction(customer, merchant, devices, base_time)
        txn["amount"] = round(amount, 2)
        txn["is_fraud"] = 1
        txn["fraud_scenario"] = scenario
        txn["timestamp"] = ts.isoformat()
        transactions.append(txn)

    elif scenario == "VELOCITY_ATTACK":
        for i in range(random.randint(5, 15)):
            txn = generate_legitimate_transaction(customer, merchant, devices, base_time)
            txn["amount"] = round(random.uniform(100, 2000), 2)
            txn["is_fraud"] = 1
            txn["fraud_scenario"] = scenario
            txn["timestamp"] = (ts + timedelta(seconds=i * random.randint(5, 60))).isoformat()
            transactions.append(txn)

    elif scenario == "NEW_DEVICE_ATTACK":
        new_device = f"DEV-NEW-{uuid.uuid4().hex[:8].upper()}"
        txn = generate_legitimate_transaction(customer, merchant, devices, base_time)
        txn["amount"] = round(random.uniform(1000, 10000), 2)
        txn["device_id"] = new_device
        txn["is_fraud"] = 1
        txn["fraud_scenario"] = scenario
        txn["timestamp"] = ts.isoformat()
        transactions.append(txn)

    elif scenario == "IMPOSSIBLE_TRAVEL":
        countries = random.sample(["US", "UK", "RU", "CN", "BR", "NG"], 2)
        for i, country in enumerate(countries):
            txn = generate_legitimate_transaction(customer, merchant, devices, base_time)
            txn["amount"] = round(random.uniform(100, 3000), 2)
            txn["country"] = country
            txn["is_fraud"] = 1
            txn["fraud_scenario"] = scenario
            txn["timestamp"] = (ts + timedelta(minutes=i * 30)).isoformat()
            transactions.append(txn)

    elif scenario == "MERCHANT_ABUSE":
        high_risk_merchant = {**merchant, "category": random.choice(["crypto_exchange", "gaming", "jewelry"])}
        for i in range(random.randint(3, 8)):
            txn = generate_legitimate_transaction(customer, high_risk_merchant, devices, base_time)
            txn["amount"] = round(random.uniform(500, 5000), 2)
            txn["merchant_category"] = high_risk_merchant["category"]
            txn["is_fraud"] = 1
            txn["fraud_scenario"] = scenario
            txn["timestamp"] = (ts + timedelta(hours=i)).isoformat()
            transactions.append(txn)

    elif scenario == "CARD_TESTING":
        for i in range(random.randint(10, 30)):
            txn = generate_legitimate_transaction(customer, merchant, devices, base_time)
            txn["amount"] = round(random.uniform(0.50, 5.00), 2)
            txn["is_fraud"] = 1
            txn["fraud_scenario"] = scenario
            txn["timestamp"] = (ts + timedelta(seconds=i * random.randint(2, 10))).isoformat()
            transactions.append(txn)

    elif scenario == "BURST_TRANSACTIONS":
        for i in range(random.randint(5, 10)):
            txn = generate_legitimate_transaction(customer, merchant, devices, base_time)
            txn["amount"] = round(random.uniform(200, 3000), 2)
            txn["is_fraud"] = 1
            txn["fraud_scenario"] = scenario
            txn["timestamp"] = (ts + timedelta(seconds=i * random.randint(1, 5))).isoformat()
            transactions.append(txn)

    return transactions


def generate_dataset(
    num_transactions: int = NUM_TRANSACTIONS,
    fraud_rate: float = FRAUD_RATE,
) -> List[Dict]:
    """Generate complete synthetic payment dataset."""
    print(f"Generating synthetic payment data: {num_transactions} transactions, {fraud_rate:.1%} fraud rate")

    customers = generate_customers(NUM_CUSTOMERS)
    merchants = generate_merchants(NUM_MERCHANTS)
    devices = generate_devices(NUM_DEVICES)
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    transactions = []
    num_fraud = int(num_transactions * fraud_rate)
    num_legit = num_transactions - num_fraud

    # Generate legitimate transactions
    for _ in range(num_legit):
        customer = random.choice(customers)
        merchant = random.choice(merchants)
        day_offset = timedelta(days=random.randint(0, 365))
        txn = generate_legitimate_transaction(customer, merchant, devices, base_time + day_offset)
        transactions.append(txn)

    # Generate fraud transactions by scenario
    scenarios = list(FRAUD_SCENARIOS.keys())
    weights = [FRAUD_SCENARIOS[s]["weight"] for s in scenarios]
    fraud_generated = 0

    while fraud_generated < num_fraud:
        scenario = random.choices(scenarios, weights=weights)[0]
        customer = random.choice(customers)
        merchant = random.choice(merchants)
        day_offset = timedelta(days=random.randint(0, 365))
        fraud_txns = generate_fraud_transaction(customer, merchant, devices, base_time + day_offset, scenario)
        for txn in fraud_txns:
            if fraud_generated >= num_fraud:
                break
            transactions.append(txn)
            fraud_generated += 1

    # Shuffle and sort by timestamp
    random.shuffle(transactions)
    transactions.sort(key=lambda x: x["timestamp"])

    return transactions


def save_dataset(transactions: List[Dict], output_path: Path):
    """Save dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "transaction_id", "customer_id", "merchant_id", "amount", "currency",
        "timestamp", "payment_method", "card_type", "device_id", "ip_address",
        "country", "merchant_category", "channel", "is_fraud", "fraud_scenario",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Saved {len(transactions)} transactions to {output_path}")


def print_summary(transactions: List[Dict]):
    """Print dataset summary."""
    total = len(transactions)
    fraud = sum(1 for t in transactions if t["is_fraud"] == 1)
    legit = total - fraud

    print(f"\n{'='*60}")
    print("SYNTHETIC PAYMENT DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"Total transactions: {total}")
    print(f"Legitimate:         {legit} ({legit/total:.1%})")
    print(f"Fraudulent:         {fraud} ({fraud/total:.1%})")

    # Scenario breakdown
    scenarios = {}
    for t in transactions:
        if t["fraud_scenario"]:
            scenarios[t["fraud_scenario"]] = scenarios.get(t["fraud_scenario"], 0) + 1
    if scenarios:
        print(f"\nFraud Scenarios:")
        for scenario, count in sorted(scenarios.items(), key=lambda x: -x[1]):
            print(f"  {scenario}: {count}")

    # Amount statistics
    amounts = [t["amount"] for t in transactions]
    fraud_amounts = [t["amount"] for t in transactions if t["is_fraud"] == 1]
    print(f"\nAmount Statistics:")
    print(f"  Overall: min=${min(amounts):.2f}, max=${max(amounts):.2f}, avg=${sum(amounts)/len(amounts):.2f}")
    if fraud_amounts:
        print(f"  Fraud:   min=${min(fraud_amounts):.2f}, max=${max(fraud_amounts):.2f}, avg=${sum(fraud_amounts)/len(fraud_amounts):.2f}")

    print(f"\n⚠️  This is SYNTHETIC data for development and testing only.")
    print(f"    Do NOT use for production fraud model training.")


if __name__ == "__main__":
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    transactions = generate_dataset()
    save_dataset(transactions, output_dir / "synthetic_payments.csv")
    print_summary(transactions)

    # Also save scenario definitions
    with open(output_dir / "fraud_scenarios.json", "w") as f:
        json.dump(FRAUD_SCENARIOS, f, indent=2)
    print(f"\nFraud scenario definitions saved to {output_dir / 'fraud_scenarios.json'}")

#!/usr/bin/env python3
"""
Demo Script — Payment Processing & Fraud Detection Platform

Demonstrates the complete decision pipeline including:
- Normal payments
- Suspicious payments
- High-risk blocked payments
- Duplicate/idempotent payments
- Fraud case creation
- Analyst feedback
"""
import json
import sys
import time
import requests

BASE_URL = "http://localhost:8000"


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_response(response):
    status = response.status_code
    data = response.json()
    emoji = "✅" if status < 400 else "❌"
    print(f"\n{emoji} Status: {status}")
    print(json.dumps(data, indent=2))
    return data


def check_health():
    print_header("HEALTH CHECK")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print_response(resp)
        return True
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Start it with:")
        print("   uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
        return False


def demo_normal_payment():
    print_header("1. NORMAL PAYMENT — Low Risk")
    payment = {
        "customer_id": "CUST-001",
        "merchant_id": "MERCH-001",
        "amount": 25.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_type": "visa",
        "device_id": "DEV-REGULAR",
        "ip_address": "192.168.1.100",
        "country": "US",
        "merchant_category": "grocery",
        "channel": "in_store",
    }
    print(f"\n📤 Sending payment: ${payment['amount']} at {payment['merchant_category']}")
    resp = requests.post(f"{BASE_URL}/payments", json=payment)
    data = print_response(resp)
    return data.get("transaction_id")


def demo_suspicious_payment():
    print_header("2. SUSPICIOUS PAYMENT — Medium Risk (Review)")
    payment = {
        "customer_id": "CUST-002",
        "merchant_id": "MERCH-050",
        "amount": 3500.00,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_type": "mastercard",
        "device_id": "DEV-MOBILE",
        "ip_address": "10.0.0.55",
        "country": "US",
        "merchant_category": "electronics",
        "channel": "online",
    }
    print(f"\n📤 Sending payment: ${payment['amount']} at {payment['merchant_category']}")
    resp = requests.post(f"{BASE_URL}/payments", json=payment)
    data = print_response(resp)
    return data.get("transaction_id")


def demo_high_risk_payment():
    print_header("3. HIGH-RISK PAYMENT — Blocked")
    payment = {
        "customer_id": "CUST-003",
        "merchant_id": "MERCH-099",
        "amount": 15000.00,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_type": "amex",
        "device_id": "DEV-NEW-UNKNOWN",
        "ip_address": "185.220.101.1",
        "country": "RU",
        "merchant_category": "crypto_exchange",
        "channel": "online",
    }
    print(f"\n📤 Sending payment: ${payment['amount']} from {payment['country']} at {payment['merchant_category']}")
    resp = requests.post(f"{BASE_URL}/payments", json=payment)
    data = print_response(resp)
    return data.get("transaction_id")


def demo_duplicate_payment(transaction_id: str):
    print_header("4. DUPLICATE PAYMENT — Idempotency Check")
    payment = {
        "transaction_id": transaction_id,
        "customer_id": "CUST-001",
        "merchant_id": "MERCH-001",
        "amount": 25.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "channel": "in_store",
    }
    print(f"\n📤 Re-sending payment with same transaction_id: {transaction_id}")
    resp = requests.post(f"{BASE_URL}/payments", json=payment)
    data = print_response(resp)
    print("\n💡 Note: Same transaction_id returns cached result (idempotency)")
    return data


def demo_fraud_check(transaction_id: str):
    print_header("5. FRAUD CHECK — Detailed Prediction")
    print(f"\n🔍 Getting fraud details for: {transaction_id}")
    resp = requests.get(f"{BASE_URL}/fraud/predictions/{transaction_id}")
    if resp.status_code == 200:
        print_response(resp)
    else:
        print(f"⚠️  No prediction available for {transaction_id}")


def demo_fraud_cases():
    print_header("6. FRAUD CASES — List Active Cases")
    resp = requests.get(f"{BASE_URL}/fraud/cases")
    data = print_response(resp)
    cases = data.get("cases", [])
    return cases


def demo_analyst_feedback(case_id: str):
    print_header("7. ANALYST FEEDBACK — Mark Case as Fraud")
    feedback = {
        "label": "FRAUD",
        "analyst_id": "ANALYST-001",
        "notes": "Confirmed fraudulent activity. Card holder reported unauthorized transaction.",
    }
    print(f"\n📝 Submitting feedback for case: {case_id}")
    resp = requests.post(f"{BASE_URL}/fraud/cases/{case_id}/feedback", json=feedback)
    print_response(resp)


def demo_case_update(case_id: str):
    print_header("8. CASE UPDATE — Block & Resolve")
    print(f"\n🔒 Blocking case: {case_id}")
    resp = requests.patch(
        f"{BASE_URL}/fraud/cases/{case_id}",
        params={"status": "BLOCKED", "analyst_id": "ANALYST-001", "notes": "Confirmed fraud - blocked"},
    )
    print_response(resp)


def demo_stats():
    print_header("9. PLATFORM STATISTICS")
    resp = requests.get(f"{BASE_URL}/fraud/stats")
    print_response(resp)


def demo_models():
    print_header("10. LOADED MODELS")
    resp = requests.get(f"{BASE_URL}/models")
    print_response(resp)


def demo_metrics():
    print_header("11. PLATFORM METRICS")
    resp = requests.get(f"{BASE_URL}/metrics")
    print_response(resp)


def main():
    print("\n" + "🚀" * 25)
    print("\n  PAYMENT PROCESSING & FRAUD DETECTION PLATFORM — DEMO")
    print("\n" + "🚀" * 25)

    # Health check
    if not check_health():
        sys.exit(1)

    time.sleep(0.5)

    # Demo scenarios
    normal_txn_id = demo_normal_payment()
    time.sleep(0.3)

    suspicious_txn_id = demo_suspicious_payment()
    time.sleep(0.3)

    blocked_txn_id = demo_high_risk_payment()
    time.sleep(0.3)

    # Duplicate payment (idempotency)
    if normal_txn_id:
        demo_duplicate_payment(normal_txn_id)
        time.sleep(0.3)

    # Fraud check details
    if blocked_txn_id:
        demo_fraud_check(blocked_txn_id)
        time.sleep(0.3)

    # Fraud cases
    cases = demo_fraud_cases()
    time.sleep(0.3)

    # Analyst workflow
    if cases:
        case_id = cases[0]["case_id"]
        demo_analyst_feedback(case_id)
        time.sleep(0.3)
        demo_case_update(case_id)
        time.sleep(0.3)

    # Statistics & metrics
    demo_stats()
    demo_models()
    demo_metrics()

    print_header("DEMO COMPLETE")
    print("\n✅ All demo scenarios executed successfully!")
    print(f"\n📊 API Documentation: {BASE_URL}/docs")
    print(f"📊 Platform Stats:    {BASE_URL}/fraud/stats")
    print(f"📊 Health Check:      {BASE_URL}/health")


if __name__ == "__main__":
    main()

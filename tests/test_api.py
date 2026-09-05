import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "models_loaded" in data

def test_fraud_stats():
    response = client.get("/fraud/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "fraud_rate" in data

def test_normal_payment():
    payment_payload = {
        "customer_id": "CUST-TEST",
        "merchant_id": "MERCH-TEST",
        "amount": 50.0,
        "currency": "USD",
        "payment_method": "credit_card",
        "channel": "online"
    }
    response = client.post("/payments", json=payment_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 50.0
    assert data["status"] in ["APPROVED", "REVIEW", "BLOCKED"]
    assert "transaction_id" in data

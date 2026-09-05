from dataclasses import dataclass
from typing import Dict, Any

# Topic Constants
TOPIC_PAYMENT_INITIATED = "payment.initiated"
TOPIC_FRAUD_CHECK_RESULT = "fraud.check.result"
TOPIC_PAYMENT_APPROVED = "payment.approved"
TOPIC_PAYMENT_BLOCKED = "payment.blocked"
TOPIC_CASE_CREATED = "case.created"

@dataclass
class PaymentInitiatedEvent:
    transaction_id: str
    customer_id: str
    merchant_id: str
    amount: float
    currency: str
    timestamp: str
    payment_method: str

@dataclass
class FraudCheckResultEvent:
    transaction_id: str
    risk_score: float
    fraud_probability: float
    decision: str
    model_version: str
    explanation: Dict[str, Any]

@dataclass
class PaymentApprovedEvent:
    transaction_id: str
    timestamp: str

@dataclass
class PaymentBlockedEvent:
    transaction_id: str
    reason: str
    timestamp: str

@dataclass
class CaseCreatedEvent:
    case_id: str
    transaction_id: str
    risk_score: float
    status: str
    timestamp: str

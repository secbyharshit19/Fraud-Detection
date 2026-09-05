from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    INITIATED = "INITIATED"
    PROCESSING = "PROCESSING"
    FRAUD_CHECK = "FRAUD_CHECK"
    APPROVED = "APPROVED"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class PaymentResponse(BaseModel):
    transaction_id: str
    status: PaymentStatus
    amount: float
    currency: str
    risk_score: Optional[int] = None
    decision: Optional[str] = None
    message: str
    created_at: datetime
    updated_at: datetime

class PaymentStateTransition(BaseModel):
    from_status: PaymentStatus
    to_status: PaymentStatus
    reason: str
    timestamp: datetime

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TriggeredRule(BaseModel):
    rule_id: str
    name: str
    severity: str
    reason: str

class TransactionRequest(BaseModel):
    transaction_id: Optional[str] = None
    customer_id: str
    merchant_id: str
    amount: float = Field(..., gt=0)
    currency: str = 'USD'
    timestamp: Optional[datetime] = None
    payment_method: str
    card_type: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    country: Optional[str] = 'US'
    merchant_category: Optional[str] = None
    channel: str = 'online'

class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    risk_score: Optional[int] = None
    decision: Optional[str] = None
    created_at: datetime

class FraudScoreResponse(BaseModel):
    transaction_id: str
    risk_score: int
    decision: str
    fraud_probability: float
    model_version: str
    feature_version: str
    triggered_rules: List[TriggeredRule]
    reasons: List[str]
    processing_time_ms: float

class PredictionResponse(BaseModel):
    transaction_id: str
    is_fraud: bool
    confidence: float
    timestamp: datetime

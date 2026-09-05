from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .transaction import TriggeredRule

class CaseStatus(str, Enum):
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"

class FeedbackLabel(str, Enum):
    FRAUD = "FRAUD"
    LEGITIMATE = "LEGITIMATE"
    UNCERTAIN = "UNCERTAIN"

class FraudCaseCreate(BaseModel):
    transaction_id: str
    risk_score: int
    decision: str
    triggered_rules: List[TriggeredRule]
    model_version: str
    explanation: str

class FraudCaseResponse(BaseModel):
    case_id: str
    transaction_id: str
    risk_score: int
    decision: str
    triggered_rules: List[TriggeredRule]
    model_version: str
    explanation: str
    status: CaseStatus
    analyst_id: Optional[str] = None
    analyst_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AnalystFeedbackRequest(BaseModel):
    label: FeedbackLabel
    notes: Optional[str] = None
    analyst_id: str

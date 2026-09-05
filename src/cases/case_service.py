import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import datetime

@dataclass
class AnalystFeedbackRequest:
    label: str
    analyst_id: str
    notes: Optional[str] = None

@dataclass
class FraudCaseResponse:
    case_id: str
    transaction_id: str
    risk_score: float
    decision: str
    triggered_rules: List[str]
    model_version: str
    explanation: Dict[str, Any]
    status: str
    analyst_id: Optional[str] = None
    analyst_notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class CaseService:
    def __init__(self):
        # In-memory storage for now
        self._cases: Dict[str, FraudCaseResponse] = {}
        self._feedback: Dict[str, List[Dict[str, Any]]] = {}

    def create_case(self, transaction_id: str, risk_score: float, decision: str, triggered_rules: List[str], model_version: str, explanation: Dict[str, Any]) -> FraudCaseResponse:
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        case = FraudCaseResponse(
            case_id=case_id,
            transaction_id=transaction_id,
            risk_score=risk_score,
            decision=decision,
            triggered_rules=triggered_rules,
            model_version=model_version,
            explanation=explanation,
            status="OPEN"
        )
        self._cases[case_id] = case
        return case

    def get_case(self, case_id: str) -> Optional[FraudCaseResponse]:
        return self._cases.get(case_id)

    def list_cases(self, status: Optional[str] = None, limit: int = 100) -> List[FraudCaseResponse]:
        cases = list(self._cases.values())
        if status:
            cases = [c for c in cases if c.status == status]
        # sort by created_at desc
        cases.sort(key=lambda x: x.created_at, reverse=True)
        return cases[:limit]

    def update_case(self, case_id: str, status: str, analyst_id: Optional[str] = None, notes: Optional[str] = None) -> Optional[FraudCaseResponse]:
        case = self.get_case(case_id)
        if not case:
            return None
        
        valid_transitions = {
            "OPEN": ["IN_PROGRESS", "CLOSED"],
            "IN_PROGRESS": ["CLOSED", "ESCALATED"],
            "ESCALATED": ["CLOSED"],
            "CLOSED": []
        }
        
        if status not in valid_transitions.get(case.status, []) and status != case.status:
            raise ValueError(f"Invalid status transition from {case.status} to {status}")
            
        case.status = status
        if analyst_id:
            case.analyst_id = analyst_id
        if notes:
            case.analyst_notes = notes
        case.updated_at = datetime.datetime.utcnow().isoformat()
        
        self._cases[case_id] = case
        return case

    def add_feedback(self, case_id: str, feedback: AnalystFeedbackRequest) -> Dict[str, Any]:
        case = self.get_case(case_id)
        if not case:
            raise ValueError("Case not found")
            
        fb_entry = {
            "transaction_id": case.transaction_id,
            "label": feedback.label,
            "analyst_id": feedback.analyst_id,
            "notes": feedback.notes,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        if case_id not in self._feedback:
            self._feedback[case_id] = []
        self._feedback[case_id].append(fb_entry)
        
        return fb_entry

    def approve_transaction(self, case_id: str, analyst_id: str) -> FraudCaseResponse:
        case = self.update_case(case_id, "CLOSED", analyst_id, "Transaction approved manually.")
        self.add_feedback(case_id, AnalystFeedbackRequest(label="legitimate", analyst_id=analyst_id, notes="Approved"))
        return case

    def block_transaction(self, case_id: str, analyst_id: str) -> FraudCaseResponse:
        case = self.update_case(case_id, "CLOSED", analyst_id, "Transaction blocked manually.")
        self.add_feedback(case_id, AnalystFeedbackRequest(label="fraud", analyst_id=analyst_id, notes="Blocked"))
        return case

    def escalate_case(self, case_id: str, analyst_id: str, reason: str) -> FraudCaseResponse:
        return self.update_case(case_id, "ESCALATED", analyst_id, f"Escalated: {reason}")

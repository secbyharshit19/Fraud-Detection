import threading
from typing import Dict, Any, List
import datetime

class MetricsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset_stats()

    def reset_stats(self):
        with self._lock:
            self._total_transactions = 0
            self._fraud_detected = 0
            self._blocked = 0
            self._under_review = 0
            self._approved = 0
            self._sum_risk_score = 0.0
            self._high_risk_count = 0
            self._sum_processing_time = 0.0
            self._error_count = 0
            self._recent_decisions = []

    def record_transaction(self, transaction_id: str, risk_score: float, decision: str, processing_time_ms: float):
        with self._lock:
            self._total_transactions += 1
            self._sum_risk_score += risk_score
            self._sum_processing_time += processing_time_ms
            
            if decision == 'fraud':
                self._fraud_detected += 1
                self._blocked += 1
            elif decision == 'review':
                self._under_review += 1
            else:
                self._approved += 1
                
            if risk_score >= 0.8:
                self._high_risk_count += 1
                
            decision_entry = {
                "transaction_id": transaction_id,
                "risk_score": risk_score,
                "decision": decision,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            self._recent_decisions.append(decision_entry)
            
            # Keep only last 50 decisions
            if len(self._recent_decisions) > 50:
                self._recent_decisions.pop(0)

    def record_error(self):
        with self._lock:
            self._error_count += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            fraud_rate = (self._fraud_detected / self._total_transactions) if self._total_transactions > 0 else 0.0
            avg_risk = (self._sum_risk_score / self._total_transactions) if self._total_transactions > 0 else 0.0
            avg_time = (self._sum_processing_time / self._total_transactions) if self._total_transactions > 0 else 0.0
            
            return {
                "total_transactions": self._total_transactions,
                "fraud_detected": self._fraud_detected,
                "fraud_rate": fraud_rate,
                "blocked": self._blocked,
                "under_review": self._under_review,
                "approved": self._approved,
                "avg_risk_score": avg_risk,
                "high_risk_count": self._high_risk_count,
                "avg_processing_time_ms": avg_time,
                "error_count": self._error_count
            }

    def get_recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            # Return copy to avoid thread issues
            return list(reversed(self._recent_decisions))[:limit]

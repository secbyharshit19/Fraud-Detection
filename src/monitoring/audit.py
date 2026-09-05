import logging
import json
import uuid
import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger('audit')
logger.setLevel(logging.INFO)

# Optional: Ensure audit logger doesn't propagate to root logger to avoid double logging
logger.propagate = False

# Setup JSON formatter for audit logs
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class AuditLogger:
    @staticmethod
    def _mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive information like full PAN or CVV."""
        masked = data.copy()
        
        # Mask card number if present (keep last 4)
        if 'card_number' in masked:
            card = str(masked['card_number'])
            if len(card) >= 4:
                masked['card_number'] = f"****-****-****-{card[-4:]}"
            else:
                masked['card_number'] = "****"
                
        # Remove CVV entirely
        if 'cvv' in masked:
            masked['cvv'] = "***"
            
        return masked

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        log_entry = {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": self._mask_sensitive_data(details)
        }
        logger.info(json.dumps(log_entry))

    def log_transaction_received(self, transaction_id: str, data: Dict[str, Any]):
        details = {
            "transaction_id": transaction_id,
            "transaction_data": data
        }
        self._log_event("TRANSACTION_RECEIVED", details)

    def log_fraud_prediction(self, transaction_id: str, risk_score: float, decision: str, model_version: str):
        details = {
            "transaction_id": transaction_id,
            "risk_score": risk_score,
            "decision": decision,
            "model_version": model_version
        }
        self._log_event("FRAUD_PREDICTION", details)

    def log_case_action(self, case_id: str, action: str, analyst_id: Optional[str] = None):
        details = {
            "case_id": case_id,
            "action": action,
            "analyst_id": analyst_id
        }
        self._log_event("CASE_ACTION", details)

    def log_model_deployment(self, model_name: str, version: str, status: str):
        details = {
            "model_name": model_name,
            "version": version,
            "status": status
        }
        self._log_event("MODEL_DEPLOYMENT", details)

    def log_status_change(self, entity_type: str, entity_id: str, old_status: str, new_status: str):
        details = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_status": old_status,
            "new_status": new_status
        }
        self._log_event("STATUS_CHANGE", details)

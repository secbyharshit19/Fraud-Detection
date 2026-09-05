from typing import List, Dict, Any, Optional
from src.schemas.transaction import TriggeredRule

class ExplanationGenerator:
    def generate_customer_explanation(self, risk_score: int, decision: str, triggered_rules: List[TriggeredRule], top_features: List[str]) -> List[str]:
        reasons = []
        for rule in triggered_rules:
            if rule.rule_id in ("R001", "R002", "R006"):
                reasons.append("Unusually high transaction amount")
            elif rule.rule_id in ("R003", "R005"):
                reasons.append("High frequency of transactions")
            elif rule.rule_id == "R004":
                reasons.append("Suspicious transaction time")
                
        # Deduplicate while preserving order
        unique_reasons = []
        for r in reasons:
            if r not in unique_reasons:
                unique_reasons.append(r)
                
        if not unique_reasons and decision != "ALLOW":
            unique_reasons.append("Automated security flag")
            
        return unique_reasons

    def generate_analyst_explanation(
        self, 
        risk_score: int, 
        decision: str, 
        triggered_rules: List[TriggeredRule], 
        model_scores: Dict[str, float], 
        feature_values: Dict[str, Any], 
        shap_values: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        return {
            "risk_score": risk_score,
            "decision": decision,
            "model_scores": model_scores,
            "rules_triggered": [r.dict() for r in triggered_rules],
            "key_features": feature_values,
            "shap_values": shap_values or {}
        }

import time
from typing import Dict, Any
from src.schemas.transaction import TransactionRequest, FraudScoreResponse, TriggeredRule
from src.fraud.thresholds import ThresholdConfig, get_decision
from src.fraud.rule_engine import RuleEngine, RuleResult
from src.fraud.risk_aggregator import RiskAggregator
from src.fraud.explanation import ExplanationGenerator

class FraudEngine:
    def __init__(
        self,
        models: Dict[str, Any],
        rule_engine: RuleEngine,
        risk_aggregator: RiskAggregator,
        explanation_generator: ExplanationGenerator,
        threshold_config: ThresholdConfig
    ):
        self.models = models or {}
        self.rule_engine = rule_engine
        self.risk_aggregator = risk_aggregator
        self.explanation_generator = explanation_generator
        self.threshold_config = threshold_config
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> FraudScoreResponse:
        start_time = time.time()
        
        # 1. Rule Engine
        rule_results = self.rule_engine.evaluate_all(transaction, features)
        total_rule_score = sum(r.score_contribution for r in rule_results)
        rule_score = min(100.0, total_rule_score)
        
        # 2. ML Models
        ml_scores = {}
        for name, model in self.models.items():
            try:
                # Assuming model has a predict_proba method that returns fraud probability
                ml_scores[name] = model.predict_proba(features)
            except Exception:
                pass
                
        # 3. Anomaly Detection
        anomaly_score = features.get("anomaly_score", 0.0)
        
        # 4. Aggregation
        if not ml_scores:
            # If no models available, rely mostly on rules
            risk_score_val = rule_score * 0.8 + anomaly_score * 0.2
            risk_score = int(min(100, max(0, risk_score_val)))
        else:
            risk_score = self.risk_aggregator.aggregate(ml_scores, rule_score, anomaly_score)
            
        # 5. Decision
        decision = get_decision(risk_score, self.threshold_config)
        
        # 6. Explanation
        triggered_schemas = [
            TriggeredRule(rule_id=r.rule_id, name=r.name, severity=r.severity, reason=r.reason)
            for r in rule_results
        ]
        
        reasons = self.explanation_generator.generate_customer_explanation(
            risk_score, decision, triggered_schemas, list(features.keys())
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return FraudScoreResponse(
            transaction_id=transaction.transaction_id or "unknown",
            risk_score=risk_score,
            decision=decision,
            fraud_probability=max(ml_scores.values()) if ml_scores else 0.0,
            model_version="v1.0" if self.models else "rules-only",
            feature_version="v1.0",
            triggered_rules=triggered_schemas,
            reasons=reasons,
            processing_time_ms=processing_time_ms
        )

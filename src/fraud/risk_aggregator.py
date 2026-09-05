from typing import Dict

class RiskAggregator:
    def __init__(self, ml_weight: float = 0.50, rule_weight: float = 0.25, anomaly_weight: float = 0.25):
        self.ml_weight = ml_weight
        self.rule_weight = rule_weight
        self.anomaly_weight = anomaly_weight
        
    def aggregate(self, ml_scores: Dict[str, float], rule_score: float, anomaly_score: float) -> int:
        """
        Aggregate scores using formula:
        final_score = ml_weight * max_ml_prob * 100 + rule_weight * rule_score + anomaly_weight * anomaly_score
        """
        max_ml_prob = max(ml_scores.values()) if ml_scores else 0.0
        
        final_score = (
            self.ml_weight * max_ml_prob * 100 +
            self.rule_weight * rule_score +
            self.anomaly_weight * anomaly_score
        )
        
        return int(max(0.0, min(100.0, final_score)))

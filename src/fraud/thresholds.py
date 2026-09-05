import os
from dataclasses import dataclass

@dataclass
class ThresholdConfig:
    review_threshold: int = 30
    block_threshold: int = 70

def get_decision(risk_score: float, config: ThresholdConfig) -> str:
    if risk_score >= config.block_threshold:
        return "BLOCK"
    elif risk_score >= config.review_threshold:
        return "REVIEW"
    return "ALLOW"

def load_thresholds_from_env() -> ThresholdConfig:
    review = int(os.getenv("RISK_THRESHOLD_REVIEW", 30))
    block = int(os.getenv("RISK_THRESHOLD_BLOCK", 70))
    return ThresholdConfig(review_threshold=review, block_threshold=block)

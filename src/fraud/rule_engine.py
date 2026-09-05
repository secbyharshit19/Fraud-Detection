import os
from typing import Optional, List, Dict, Any
from src.schemas.transaction import TransactionRequest
from pydantic import BaseModel

class RuleResult(BaseModel):
    rule_id: str
    name: str
    severity: str
    reason: str
    score_contribution: float

class FraudRule:
    def __init__(self, rule_id: str, name: str, severity: str):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> Optional[RuleResult]:
        raise NotImplementedError

class HighAmountRule(FraudRule):
    def __init__(self, threshold: float = 5000):
        super().__init__("R001", "HIGH_AMOUNT", "MEDIUM")
        self.threshold = threshold
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> Optional[RuleResult]:
        if transaction.amount > self.threshold:
            return RuleResult(
                rule_id=self.rule_id,
                name=self.name,
                severity=self.severity,
                reason=f"Amount {transaction.amount} exceeds high amount threshold {self.threshold}",
                score_contribution=20.0
            )
        return None

class VeryHighAmountRule(FraudRule):
    def __init__(self, threshold: float = 10000):
        super().__init__("R002", "VERY_HIGH_AMOUNT", "HIGH")
        self.threshold = threshold
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> Optional[RuleResult]:
        if transaction.amount > self.threshold:
            return RuleResult(
                rule_id=self.rule_id,
                name=self.name,
                severity=self.severity,
                reason=f"Amount {transaction.amount} exceeds very high amount threshold {self.threshold}",
                score_contribution=40.0
            )
        return None

class HighVelocityRule(FraudRule):
    def __init__(self, threshold: int = 10):
        super().__init__("R003", "HIGH_VELOCITY", "HIGH")
        self.threshold = threshold
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> Optional[RuleResult]:
        count = features.get("transaction_count_1h", 0)
        if count > self.threshold:
            return RuleResult(
                rule_id=self.rule_id,
                name=self.name,
                severity=self.severity,
                reason=f"Transaction count {count}/hr exceeds threshold {self.threshold}",
                score_contribution=30.0
            )
        return None

class NightHighAmountRule(FraudRule):
    def __init__(self, threshold: float = 2000):
        super().__init__("R004", "NIGHT_HIGH_AMOUNT", "HIGH")
        self.threshold = threshold
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> Optional[RuleResult]:
        is_night = features.get("is_night", False)
        if is_night and transaction.amount > self.threshold:
            return RuleResult(
                rule_id=self.rule_id,
                name=self.name,
                severity=self.severity,
                reason=f"Night transaction amount {transaction.amount} exceeds threshold {self.threshold}",
                score_contribution=35.0
            )
        return None

class RapidSuccessionRule(FraudRule):
    def __init__(self, threshold: int = 30):
        super().__init__("R005", "RAPID_SUCCESSION", "HIGH")
        self.threshold = threshold
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> Optional[RuleResult]:
        time_since = features.get("time_since_prev")
        if time_since is not None and time_since < self.threshold:
            return RuleResult(
                rule_id=self.rule_id,
                name=self.name,
                severity=self.severity,
                reason=f"Time since previous transaction {time_since}s is less than {self.threshold}s",
                score_contribution=30.0
            )
        return None

class SuspiciousAmountRule(FraudRule):
    def __init__(self, threshold: float = 3.0):
        super().__init__("R006", "SUSPICIOUS_AMOUNT", "MEDIUM")
        self.threshold = threshold
        
    def evaluate(self, transaction: TransactionRequest, features: Dict[str, Any]) -> Optional[RuleResult]:
        zscore = features.get("amount_zscore")
        if zscore is not None and zscore > self.threshold:
            return RuleResult(
                rule_id=self.rule_id,
                name=self.name,
                severity=self.severity,
                reason=f"Amount z-score {zscore:.2f} exceeds threshold {self.threshold}",
                score_contribution=25.0
            )
        return None

class RuleEngine:
    def __init__(self):
        self.rules: List[FraudRule] = []
        
    def register_rule(self, rule: FraudRule) -> None:
        self.rules.append(rule)
        
    def evaluate_all(self, transaction: TransactionRequest, features: Dict[str, Any]) -> List[RuleResult]:
        results = []
        for rule in self.rules:
            result = rule.evaluate(transaction, features)
            if result:
                results.append(result)
        return results

def get_default_rule_engine() -> RuleEngine:
    engine = RuleEngine()
    engine.register_rule(HighAmountRule(float(os.getenv("RULE_R001_THRESHOLD", 5000))))
    engine.register_rule(VeryHighAmountRule(float(os.getenv("RULE_R002_THRESHOLD", 10000))))
    engine.register_rule(HighVelocityRule(int(os.getenv("RULE_R003_THRESHOLD", 10))))
    engine.register_rule(NightHighAmountRule(float(os.getenv("RULE_R004_THRESHOLD", 2000))))
    engine.register_rule(RapidSuccessionRule(int(os.getenv("RULE_R005_THRESHOLD", 30))))
    engine.register_rule(SuspiciousAmountRule(float(os.getenv("RULE_R006_THRESHOLD", 3.0))))
    return engine

from src.schemas.payment import PaymentStatus

class InvalidTransition(Exception):
    pass

class PaymentStateMachine:
    def __init__(self):
        self.transitions = {
            PaymentStatus.INITIATED: [PaymentStatus.PROCESSING, PaymentStatus.FAILED],
            PaymentStatus.PROCESSING: [PaymentStatus.FRAUD_CHECK, PaymentStatus.FAILED],
            PaymentStatus.FRAUD_CHECK: [PaymentStatus.APPROVED, PaymentStatus.REVIEW, PaymentStatus.BLOCKED],
            PaymentStatus.APPROVED: [PaymentStatus.COMPLETED],
            PaymentStatus.REVIEW: [PaymentStatus.APPROVED, PaymentStatus.BLOCKED, PaymentStatus.FRAUD_CHECK],
            PaymentStatus.BLOCKED: [PaymentStatus.REVIEW],
            PaymentStatus.COMPLETED: [],
            PaymentStatus.FAILED: []
        }
        
    def transition(self, current: PaymentStatus, target: PaymentStatus) -> PaymentStatus:
        valid_next_states = self.get_valid_transitions(current)
        if target not in valid_next_states:
            raise InvalidTransition(f"Cannot transition from {current} to {target}")
        return target
        
    def get_valid_transitions(self, current: PaymentStatus) -> list[PaymentStatus]:
        return self.transitions.get(current, [])

import uuid
from datetime import datetime, timezone
from src.schemas.transaction import TransactionRequest
from src.schemas.payment import PaymentResponse, PaymentStatus
from src.payment.payment_state import PaymentStateMachine
from src.payment.idempotency import IdempotencyManager
from src.payment.transaction_service import InMemoryTransactionStore
from typing import Optional, Any

class PaymentService:
    def __init__(
        self,
        fraud_engine: Any,
        idempotency_manager: IdempotencyManager,
        transaction_store: InMemoryTransactionStore
    ):
        self.fraud_engine = fraud_engine
        self.idempotency_manager = idempotency_manager
        self.transaction_store = transaction_store
        self.state_machine = PaymentStateMachine()
        
    def process_payment(self, request: TransactionRequest) -> PaymentResponse:
        # Generate transaction_id if not provided
        if not request.transaction_id:
            request.transaction_id = str(uuid.uuid4())
            
        # Check idempotency
        idempotency_key = self.idempotency_manager.generate_idempotency_key(
            request.transaction_id, request.customer_id
        )
        cached_result = self.idempotency_manager.check_idempotency(idempotency_key)
        if cached_result:
            return PaymentResponse(**cached_result)
            
        self.transaction_store.save_transaction(request)
        
        # State transitions
        current_state = PaymentStatus.INITIATED
        current_state = self.state_machine.transition(current_state, PaymentStatus.PROCESSING)
        current_state = self.state_machine.transition(current_state, PaymentStatus.FRAUD_CHECK)
        
        # Call fraud engine
        features = {}  # In a real system, we would gather features here
        fraud_result = self.fraud_engine.evaluate(request, features)
        
        # Determine next state based on decision
        decision = fraud_result.decision
        if decision == "ALLOW":
            next_state = PaymentStatus.APPROVED
            message = "Payment approved"
        elif decision == "REVIEW":
            next_state = PaymentStatus.REVIEW
            message = "Payment under review"
        else:
            next_state = PaymentStatus.BLOCKED
            message = "Payment blocked due to high risk"
            
        current_state = self.state_machine.transition(current_state, next_state)
        
        now = datetime.now(timezone.utc)
        response = PaymentResponse(
            transaction_id=request.transaction_id,
            status=current_state,
            amount=request.amount,
            currency=request.currency,
            risk_score=fraud_result.risk_score,
            decision=decision,
            message=message,
            created_at=now,
            updated_at=now
        )
        
        self.transaction_store.save_payment(response)
        self.idempotency_manager.store_result(idempotency_key, response.dict())
        
        return response
        
    def get_payment(self, transaction_id: str) -> Optional[PaymentResponse]:
        return self.transaction_store.get_payment(transaction_id)

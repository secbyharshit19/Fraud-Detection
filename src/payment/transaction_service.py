from typing import Dict, List, Optional
from src.schemas.transaction import TransactionRequest
from src.schemas.payment import PaymentResponse

class InMemoryTransactionStore:
    def __init__(self):
        self.transactions: Dict[str, TransactionRequest] = {}
        self.payments: Dict[str, PaymentResponse] = {}
        
    def save_transaction(self, request: TransactionRequest) -> None:
        if request.transaction_id:
            self.transactions[request.transaction_id] = request
            
    def get_transaction(self, transaction_id: str) -> Optional[TransactionRequest]:
        return self.transactions.get(transaction_id)
        
    def save_payment(self, payment: PaymentResponse) -> None:
        self.payments[payment.transaction_id] = payment
        
    def get_payment(self, transaction_id: str) -> Optional[PaymentResponse]:
        return self.payments.get(transaction_id)
        
    def list_transactions(self) -> List[TransactionRequest]:
        return list(self.transactions.values())

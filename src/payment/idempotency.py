import hashlib
from typing import Optional, Dict, Any

class IdempotencyManager:
    def check_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def store_result(self, key: str, result: Dict[str, Any], ttl: int = 86400) -> None:
        raise NotImplementedError
        
    def generate_idempotency_key(self, transaction_id: str, customer_id: str) -> str:
        data = f"{transaction_id}_{customer_id}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()

class InMemoryIdempotencyManager(IdempotencyManager):
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def check_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(key)
        
    def store_result(self, key: str, result: Dict[str, Any], ttl: int = 86400) -> None:
        self._cache[key] = result

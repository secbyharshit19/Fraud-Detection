import json
import logging
import redis
from typing import Optional, Dict, Any

from src.config.settings import RedisConfig

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client for caching and velocity checks."""
    
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=RedisConfig.HOST,
                port=RedisConfig.PORT,
                db=RedisConfig.DB,
                password=RedisConfig.PASSWORD,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            self._is_available = True
        except redis.ConnectionError as e:
            logger.warning(f"Redis unavailable, running in degraded mode: {e}")
            self.client = None
            self._is_available = False

    def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            return self.client.ping()
        except redis.ConnectionError:
            self._is_available = False
            return False

    def get_cached_prediction(self, transaction_id: str) -> Optional[dict]:
        if not self._is_available:
            return None
        try:
            key = f"fraud:pred:{transaction_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    def cache_prediction(self, transaction_id: str, data: dict, ttl: int = 3600) -> None:
        if not self._is_available:
            return
        try:
            key = f"fraud:pred:{transaction_id}"
            self.client.setex(key, ttl, json.dumps(data))
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis set failed: {e}")

    def check_idempotency(self, key: str) -> Optional[dict]:
        if not self._is_available:
            return None
        try:
            rkey = f"fraud:idem:{key}"
            data = self.client.get(rkey)
            return json.loads(data) if data else None
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    def store_idempotency(self, key: str, result: dict, ttl: int = 3600) -> None:
        if not self._is_available:
            return
        try:
            rkey = f"fraud:idem:{key}"
            self.client.setex(rkey, ttl, json.dumps(result))
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis set failed: {e}")

    def increment_velocity(self, customer_id: str, window_seconds: int = 3600) -> int:
        if not self._is_available:
            return 0
        try:
            key = f"fraud:vel:{customer_id}"
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = pipe.execute()
            return int(results[0])
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis incr failed: {e}")
            return 0

    def get_velocity(self, customer_id: str, window_seconds: int = 3600) -> int:
        if not self._is_available:
            return 0
        try:
            key = f"fraud:vel:{customer_id}"
            val = self.client.get(key)
            return int(val) if val else 0
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis get velocity failed: {e}")
            return 0

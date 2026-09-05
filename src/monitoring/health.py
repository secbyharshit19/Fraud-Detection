import time
import os
from typing import Dict, Any, List

class HealthChecker:
    @staticmethod
    def check_redis(redis_client) -> Dict[str, Any]:
        start = time.time()
        is_healthy = redis_client.health_check() if redis_client else False
        latency = (time.time() - start) * 1000 if is_healthy else None
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "latency_ms": latency
        }

    @staticmethod
    def check_database(db_manager) -> Dict[str, Any]:
        start = time.time()
        is_healthy = db_manager.health_check() if db_manager else False
        latency = (time.time() - start) * 1000 if is_healthy else None
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "latency_ms": latency
        }

    @staticmethod
    def check_kafka(kafka_producer) -> Dict[str, Any]:
        # Simple check based on producer availability flag
        is_healthy = kafka_producer._is_available if kafka_producer else False
        return {
            "status": "healthy" if is_healthy else "unhealthy"
        }

    @staticmethod
    def check_models(model_paths: List[str]) -> Dict[str, Any]:
        loaded_models = []
        missing_models = []
        
        for path in model_paths:
            if os.path.exists(path):
                loaded_models.append(path)
            else:
                missing_models.append(path)
                
        return {
            "loaded_models": loaded_models,
            "missing_models": missing_models,
            "status": "healthy" if not missing_models else "degraded"
        }

    def full_health_check(self, redis_client=None, db_manager=None, kafka_producer=None, model_paths=None) -> Dict[str, Any]:
        model_paths = model_paths or []
        
        redis_health = self.check_redis(redis_client)
        db_health = self.check_database(db_manager)
        kafka_health = self.check_kafka(kafka_producer)
        models_health = self.check_models(model_paths)
        
        is_fully_healthy = (
            redis_health["status"] == "healthy" and
            db_health["status"] == "healthy" and
            kafka_health["status"] == "healthy" and
            models_health["status"] == "healthy"
        )
        
        return {
            "status": "healthy" if is_fully_healthy else "degraded",
            "components": {
                "redis": redis_health,
                "database": db_health,
                "kafka": kafka_health,
                "models": models_health
            }
        }

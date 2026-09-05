import json
import logging
from typing import List, Callable, Dict, Any
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from src.config.settings import KafkaConfig

logger = logging.getLogger(__name__)

class FraudKafkaConsumer:
    def __init__(self, group_id: str):
        self._is_available = True
        self.group_id = group_id
        try:
            self.consumer = KafkaConsumer(
                bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                client_id=KafkaConfig.CLIENT_ID,
                value_deserializer=lambda v: self._safe_deserialize(v),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                session_timeout_ms=10000
            )
        except KafkaError as e:
            logger.warning(f"Kafka consumer unavailable: {e}")
            self.consumer = None
            self._is_available = False

    def _safe_deserialize(self, value: bytes) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Poison pill skipped. Failed to deserialize message: {e}")
            return None

    def subscribe(self, topics: List[str]):
        if self._is_available and self.consumer:
            self.consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {topics}")

    def process_message(self, message, handler_func: Callable) -> bool:
        """Process a single message and return whether it was handled successfully."""
        try:
            if message.value is None:
                logger.warning(f"Skipped message with None value at offset {message.offset}")
                return True # Treat as processed to move past poison pill

            handler_func(message.topic, message.key, message.value)
            return True
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False

    def consume_loop(self, handler_func: Callable):
        if not self._is_available or not self.consumer:
            logger.error("Consumer is not available. Exiting loop.")
            return

        logger.info(f"Starting consumer loop for group {self.group_id}")
        try:
            for message in self.consumer:
                success = self.process_message(message, handler_func)
                if success:
                    self.consumer.commit()
        except KeyboardInterrupt:
            logger.info("Consumer loop interrupted by user.")
        except Exception as e:
            logger.error(f"Unexpected error in consumer loop: {e}")
        finally:
            self.close()

    def close(self):
        if self._is_available and self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed.")

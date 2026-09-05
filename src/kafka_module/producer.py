import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

from src.config.settings import KafkaConfig
from src.kafka_module.topics import (
    TOPIC_PAYMENT_INITIATED,
    TOPIC_FRAUD_CHECK_RESULT,
    TOPIC_CASE_CREATED
)

logger = logging.getLogger(__name__)

class FraudKafkaProducer:
    def __init__(self):
        self._is_available = True
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
                client_id=KafkaConfig.CLIENT_ID,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                retries=3,
                request_timeout_ms=5000,
                max_block_ms=5000
            )
            # Test connectivity
            self.producer.partitions_for(TOPIC_PAYMENT_INITIATED)
        except KafkaError as e:
            logger.warning(f"Kafka unavailable, running in degraded mode: {e}")
            self.producer = None
            self._is_available = False

    def send_event(self, topic: str, key: str, value: Dict[str, Any]) -> bool:
        if not self._is_available or not self.producer:
            logger.debug(f"Kafka degraded. Event not sent: {topic} - {key}")
            return False
            
        try:
            def on_send_success(record_metadata):
                logger.info(f"Sent event to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")

            def on_send_error(excp):
                logger.error(f"Failed to send event: {excp}")

            future = self.producer.send(topic, key=key, value=value)
            future.add_callback(on_send_success)
            future.add_errback(on_send_error)
            return True
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            return False

    def send_payment_initiated(self, transaction_data: Dict[str, Any]) -> bool:
        return self.send_event(
            topic=TOPIC_PAYMENT_INITIATED,
            key=str(transaction_data.get('transaction_id')),
            value=transaction_data
        )

    def send_fraud_check_result(self, transaction_id: str, result: Dict[str, Any]) -> bool:
        return self.send_event(
            topic=TOPIC_FRAUD_CHECK_RESULT,
            key=str(transaction_id),
            value=result
        )

    def send_case_created(self, case_data: Dict[str, Any]) -> bool:
        return self.send_event(
            topic=TOPIC_CASE_CREATED,
            key=str(case_data.get('case_id')),
            value=case_data
        )

    def flush(self):
        if self._is_available and self.producer:
            self.producer.flush()

    def close(self):
        if self._is_available and self.producer:
            self.producer.close()

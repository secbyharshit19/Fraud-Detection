import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", DATA_DIR / "creditcard.csv"))
PROCESSED_DATA_DIR = Path(os.getenv("PROCESSED_DATA_DIR", DATA_DIR / "processed"))
FEEDBACK_DATA_DIR = Path(os.getenv("FEEDBACK_DATA_DIR", DATA_DIR / "feedback"))
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", BASE_DIR / "artifacts"))

# Create necessary directories
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
class RedisConfig:
    HOST = os.getenv('REDIS_HOST', 'localhost')
    PORT = int(os.getenv('REDIS_PORT', 6379))
    DB = int(os.getenv('REDIS_DB', 0))
    PASSWORD = os.getenv('REDIS_PASSWORD', None)

class KafkaConfig:
    BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    CLIENT_ID = os.getenv('KAFKA_CLIENT_ID', 'fraud-detection-client')
    SECURITY_PROTOCOL = os.getenv('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT')

class DatabaseConfig:
    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', 5432))
    NAME = os.getenv('DB_NAME', 'fraud_db')
    USER = os.getenv('DB_USER', 'postgres')
    PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    MIN_CONNS = int(os.getenv('DB_MIN_CONNS', 1))
    MAX_CONNS = int(os.getenv('DB_MAX_CONNS', 10))

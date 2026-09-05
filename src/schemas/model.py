from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum

class ModelStatus(str, Enum):
    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    RETIRED = "RETIRED"

class ModelInfo(BaseModel):
    model_name: str
    version: str
    algorithm: str
    training_date: datetime
    features: List[str]
    dataset_version: str
    metrics: Dict[str, Any]
    threshold: float
    artifact_path: str
    status: ModelStatus

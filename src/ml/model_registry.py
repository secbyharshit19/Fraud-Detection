import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    name: str
    version: str
    algorithm: str
    features: List[str]
    metrics: Dict[str, float]
    threshold: float
    artifact_path: str
    status: str
    created_at: str
    updated_at: str

class ModelRegistry:
    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            registry_dir = repo_root / "models" / "registry"
            registry_dir.mkdir(parents=True, exist_ok=True)
            self.registry_path = registry_dir / "registry.json"
        else:
            self.registry_path = Path(registry_path)
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
        self.models: Dict[str, ModelInfo] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.models[k] = ModelInfo(**v)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")

    def _save_registry(self) -> None:
        try:
            with open(self.registry_path, "w") as f:
                json.dump({k: asdict(v) for k, v in self.models.items()}, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def register_model(
        self, 
        name: str, 
        version: str, 
        algorithm: str, 
        features: List[str], 
        metrics: Dict[str, float], 
        threshold: float, 
        artifact_path: str, 
        status: str = "TRAINING"
    ) -> None:
        """Registers a new model in the registry."""
        model_id = f"{name}_{version}"
        now = datetime.now().isoformat()
        
        info = ModelInfo(
            name=name,
            version=version,
            algorithm=algorithm,
            features=features,
            metrics=metrics,
            threshold=threshold,
            artifact_path=artifact_path,
            status=status,
            created_at=now,
            updated_at=now
        )
        
        self.models[model_id] = info
        self._save_registry()
        logger.info(f"Model {model_id} registered with status {status}.")

    def promote_model(self, name: str, version: str, new_status: str) -> None:
        """Promotes a model to a new status (e.g., TRAINING -> VALIDATION -> STAGING -> PRODUCTION)."""
        model_id = f"{name}_{version}"
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found in registry.")
            
        if new_status == "PRODUCTION":
            # Demote any existing production model for the same name
            for m_id, m_info in self.models.items():
                if m_info.name == name and m_info.status == "PRODUCTION" and m_id != model_id:
                    m_info.status = "ARCHIVED"
                    m_info.updated_at = datetime.now().isoformat()
                    logger.info(f"Demoted {m_id} to ARCHIVED.")
                    
        self.models[model_id].status = new_status
        self.models[model_id].updated_at = datetime.now().isoformat()
        self._save_registry()
        logger.info(f"Model {model_id} promoted to {new_status}.")

    def get_production_model(self, name: str) -> Optional[ModelInfo]:
        """Returns the current production model for the given name."""
        for m_info in self.models.values():
            if m_info.name == name and m_info.status == "PRODUCTION":
                return m_info
        return None

    def list_models(self) -> List[ModelInfo]:
        """Returns all registered models."""
        return list(self.models.values())

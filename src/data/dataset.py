import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

@dataclass
class DatasetVersion:
    version: str
    date: str
    split_method: str
    feature_version: str
    stats: Dict[str, Any]

def save_dataset_metadata(metadata: DatasetVersion, output_path: Path):
    """Save dataset metadata to JSON."""
    with open(output_path, 'w') as f:
        json.dump(asdict(metadata), f, indent=4)

def load_dataset_metadata(input_path: Path) -> DatasetVersion:
    """Load dataset metadata from JSON."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    return DatasetVersion(**data)

def create_training_metadata(version: str, split_method: str, stats: Dict[str, Any]) -> DatasetVersion:
    """Helper to create metadata object."""
    return DatasetVersion(
        version=version,
        date=datetime.now().isoformat(),
        split_method=split_method,
        feature_version="v1",
        stats=stats
    )

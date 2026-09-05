import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Feature list as per documentation
FEATURE_COLUMNS = [f"V{i}" for i in range(1, 29)] + [
    "Amount", "hour", "dayofweek", "is_weekend", "is_night", "log_amount",
    "amount_zscore", "transaction_count_1h", "transaction_count_24h",
    "amount_sum_1h", "amount_sum_24h", "amount_mean_1h", "time_since_prev",
    "risk_score"
]

def train_model(X_train: pd.DataFrame, y_train: pd.Series, params: Dict[str, Any]) -> XGBClassifier:
    """Trains an XGBoost classifier with the given parameters."""
    logger.info("Initializing XGBoost classifier...")
    
    # Auto-compute scale_pos_weight if needed
    if params.get("scale_pos_weight") == "auto-computed":
        pos_count = max(y_train.sum(), 1)
        neg_count = len(y_train) - pos_count
        params["scale_pos_weight"] = neg_count / pos_count
        logger.info(f"Auto-computed scale_pos_weight: {params['scale_pos_weight']:.2f}")

    model = XGBClassifier(**params, random_state=42)
    
    logger.info("Training model...")
    model.fit(X_train, y_train)
    logger.info("Model training completed.")
    
    return model

def evaluate_model(model: XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluates the model on test data and returns metrics."""
    logger.info("Evaluating model...")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_pred_proba)),
        "pr_auc": float(average_precision_score(y_test, y_pred_proba)),
    }
    
    logger.info(f"Evaluation metrics: {metrics}")
    return metrics

def save_model(model: XGBClassifier, path: str, metadata: Dict[str, Any]) -> None:
    """Saves the model to the specified path along with its metadata."""
    logger.info(f"Saving model to {path}...")
    model_path = Path(path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    import joblib
    joblib.dump(model, model_path)
    
    # Save metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata_filename = f"{model_path.stem}_{timestamp}_metadata.json"
    
    # Save in artifacts/training_runs/ by default if not specified otherwise
    repo_root = Path(__file__).resolve().parent.parent.parent
    metadata_dir = repo_root / "artifacts" / "training_runs"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = metadata_dir / metadata_filename
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
    logger.info(f"Metadata saved to {metadata_path}")

def run_pipeline() -> None:
    """Loads data, trains the model, evaluates it, and saves the artifacts."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    processed_data_dir = repo_root / "data" / "processed"
    
    try:
        X_train = pd.read_parquet(processed_data_dir / "X_train_scaled.parquet")
        y_train = pd.read_parquet(processed_data_dir / "y_train.parquet").iloc[:, 0]
        X_test = pd.read_parquet(processed_data_dir / "X_test_scaled.parquet")
        y_test = pd.read_parquet(processed_data_dir / "y_test.parquet").iloc[:, 0]
    except FileNotFoundError:
        logger.error("Processed data not found. Please run the data pipeline first.")
        return

    # Filter features
    available_features = [f for f in FEATURE_COLUMNS if f in X_train.columns]
    X_train = X_train[available_features]
    X_test = X_test[available_features]

    hyperparameters = {
        "n_estimators": 500,
        "max_depth": 8,
        "learning_rate": 0.05,
        "min_child_weight": 5,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "scale_pos_weight": "auto-computed"
    }

    model = train_model(X_train, y_train, hyperparameters)
    metrics = evaluate_model(model, X_test, y_test)
    
    metadata = {
        "model_type": "XGBoost",
        "hyperparameters": {k: v for k, v in model.get_params().items() if v is not None},
        "features": available_features,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    model_save_path = repo_root / "models" / "trained" / "xgboost_v1.pkl"
    save_model(model, str(model_save_path), metadata)

if __name__ == "__main__":
    run_pipeline()

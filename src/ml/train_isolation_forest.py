import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
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

FEATURE_COLUMNS = [f"V{i}" for i in range(1, 29)] + [
    "Amount", "hour", "dayofweek", "is_weekend", "is_night", "log_amount",
    "amount_zscore", "transaction_count_1h", "transaction_count_24h",
    "amount_sum_1h", "amount_sum_24h", "amount_mean_1h", "time_since_prev",
    "risk_score"
]

class IsolationForestWrapper:
    """Wrapper for IsolationForest to provide a consistent API and normalized scores."""
    
    def __init__(self, **params):
        self.model = IsolationForest(**params)
        self.min_score_ = None
        self.max_score_ = None
        self.params = params

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        """Fits the IsolationForest model."""
        self.model.fit(X)
        # Compute baseline scores for normalization
        scores = self.model.decision_function(X)
        # Isolation forest returns negative values for anomalies, positive for normal
        # We invert it so higher is more anomalous
        inverted_scores = -scores
        self.min_score_ = np.min(inverted_scores)
        self.max_score_ = np.max(inverted_scores)
        return self

    def predict_anomaly_score(self, X: pd.DataFrame) -> np.ndarray:
        """Returns normalized anomaly scores in range [0, 100]."""
        scores = self.model.decision_function(X)
        inverted_scores = -scores
        
        # Normalize to 0-100
        if self.max_score_ == self.min_score_:
            normalized = np.zeros_like(inverted_scores)
        else:
            normalized = 100 * (inverted_scores - self.min_score_) / (self.max_score_ - self.min_score_)
        
        return np.clip(normalized, 0, 100)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Returns -1 for anomaly, 1 for normal."""
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Returns pseudo-probabilities for compatibility [legit_prob, fraud_prob]."""
        scores = self.predict_anomaly_score(X)
        fraud_prob = scores / 100.0
        legit_prob = 1.0 - fraud_prob
        return np.column_stack((legit_prob, fraud_prob))
        
    def get_params(self, deep=True):
        return self.params

def train_model(X_train: pd.DataFrame, params: Dict[str, Any]) -> IsolationForestWrapper:
    """Trains an IsolationForest model with the given parameters."""
    logger.info("Initializing IsolationForest...")
    
    model = IsolationForestWrapper(**params, random_state=42)
    
    logger.info("Training model...")
    # Isolation Forest is unsupervised, so we don't need y_train
    model.fit(X_train)
    logger.info("Model training completed.")
    
    return model

def evaluate_model(model: IsolationForestWrapper, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluates the model on test data and returns metrics."""
    logger.info("Evaluating model...")
    # IF returns -1 for anomaly, 1 for normal. We need 1 for fraud, 0 for normal
    y_pred_if = model.predict(X_test)
    y_pred = np.where(y_pred_if == -1, 1, 0)
    
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

def save_model(model: IsolationForestWrapper, path: str, metadata: Dict[str, Any]) -> None:
    """Saves the model to the specified path along with its metadata."""
    logger.info(f"Saving model to {path}...")
    model_path = Path(path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    import joblib
    joblib.dump(model, model_path)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata_filename = f"{model_path.stem}_{timestamp}_metadata.json"
    
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
        X_test = pd.read_parquet(processed_data_dir / "X_test_scaled.parquet")
        y_test = pd.read_parquet(processed_data_dir / "y_test.parquet").iloc[:, 0]
    except FileNotFoundError:
        logger.error("Processed data not found. Please run the data pipeline first.")
        return

    available_features = [f for f in FEATURE_COLUMNS if f in X_train.columns]
    X_train = X_train[available_features]
    X_test = X_test[available_features]

    hyperparameters = {
        "n_estimators": 200,
        "contamination": 0.002,
        "max_features": 0.8
    }

    model = train_model(X_train, hyperparameters)
    metrics = evaluate_model(model, X_test, y_test)
    
    metadata = {
        "model_type": "IsolationForest",
        "hyperparameters": model.get_params(),
        "features": available_features,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    model_save_path = repo_root / "models" / "trained" / "isolation_forest_v1.pkl"
    save_model(model, str(model_save_path), metadata)

if __name__ == "__main__":
    run_pipeline()

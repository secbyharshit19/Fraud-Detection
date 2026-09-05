import json
import logging
from pathlib import Path
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
    precision_recall_curve,
    roc_curve
)

logger = logging.getLogger(__name__)

def evaluate_binary_classifier(model: Any, X_test: pd.DataFrame, y_test: pd.Series, model_name: str) -> Dict[str, float]:
    """Evaluates a binary classifier and returns a dictionary of metrics."""
    # Handle IsolationForest separately if it doesn't have standard predict behavior
    if hasattr(model, 'predict_anomaly_score'):
        # Wrapper logic
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred_if = model.predict(X_test)
        y_pred = np.where(y_pred_if == -1, 1, 0)
    else:
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    metrics = {
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_pred_proba)),
        "pr_auc": float(average_precision_score(y_test, y_pred_proba)),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0,
    }
    return metrics

def evaluate_at_thresholds(model: Any, X_test: pd.DataFrame, y_test: pd.Series, thresholds: List[float]) -> pd.DataFrame:
    """Evaluates model performance at different prediction thresholds."""
    if hasattr(model, 'predict_proba'):
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    elif hasattr(model, 'predict_anomaly_score'):
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    else:
        raise ValueError("Model must have predict_proba method.")

    results = []
    for threshold in thresholds:
        y_pred = (y_pred_proba >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        
        results.append({
            "threshold": threshold,
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
            "true_negatives": tn
        })
        
    return pd.DataFrame(results)

def print_evaluation_report(metrics: Dict[str, float], model_name: str) -> None:
    """Prints a formatted evaluation report."""
    print(f"--- Evaluation Report for {model_name} ---")
    for metric, value in metrics.items():
        print(f"{metric.replace('_', ' ').title()}: {value:.4f}")
    print("-" * 40)

def plot_metrics(metrics_dict: Dict[str, Dict[str, float]]) -> None:
    """
    Saves metrics plots.
    Since we only have the final metrics dict here and not the raw predictions,
    this creates a bar chart comparing models.
    (To plot ROC and PR curves properly, the full probas would be needed).
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(metrics_dict).T
    
    # Plot PR AUC and ROC AUC
    fig, ax = plt.subplots(figsize=(10, 6))
    df[['pr_auc', 'roc_auc']].plot(kind='bar', ax=ax)
    plt.title('Model Comparison - PR AUC & ROC AUC')
    plt.ylabel('Score')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(reports_dir / 'auc_comparison.png')
    plt.close()

def compare_models(models_dict: Dict[str, Any], X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
    """Compares multiple models on the test set."""
    results = {}
    for name, model in models_dict.items():
        results[name] = evaluate_binary_classifier(model, X_test, y_test, name)
        
    df = pd.DataFrame(results).T
    
    repo_root = Path(__file__).resolve().parent.parent.parent
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(reports_dir / "model_comparison.csv")
    
    return df

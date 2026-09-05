import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

logger = logging.getLogger(__name__)

@dataclass
class ThresholdResult:
    optimal_threshold: float
    min_cost: float
    evaluated_thresholds: pd.DataFrame

def optimize_threshold(
    model: Any, 
    X_val: pd.DataFrame, 
    y_val: pd.Series, 
    fraud_loss_cost: float = 100.0, 
    false_positive_cost: float = 10.0, 
    review_cost: float = 5.0
) -> ThresholdResult:
    """
    Optimizes the decision threshold to minimize total business cost.
    Evaluates thresholds from 0.05 to 0.95 in steps of 0.05.
    """
    logger.info("Optimizing threshold based on business costs...")
    
    if hasattr(model, 'predict_proba'):
        y_pred_proba = model.predict_proba(X_val)[:, 1]
    elif hasattr(model, 'predict_anomaly_score'):
        y_pred_proba = model.predict_proba(X_val)[:, 1]
    else:
        raise ValueError("Model must have predict_proba method.")

    thresholds = np.arange(0.05, 1.00, 0.05)
    results = []
    
    total_transactions = len(y_val)
    
    for threshold in thresholds:
        y_pred = (y_pred_proba >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_val, y_pred).ravel()
        
        # In a real scenario, approval vs review vs block might be separate thresholds.
        # Here we assume: 
        # Predicted Fraud -> Block (cost = fp * false_positive_cost) 
        # Predicted Normal -> Approve (cost = fn * fraud_loss_cost)
        # For review cost, let's say all blocked transactions require review (fp + tp) * review_cost
        
        cost_false_negatives = fn * fraud_loss_cost
        cost_false_positives = fp * false_positive_cost
        cost_reviews = (fp + tp) * review_cost
        
        total_cost = cost_false_negatives + cost_false_positives + cost_reviews
        
        precision = precision_score(y_val, y_pred, zero_division=0)
        recall = recall_score(y_val, y_pred, zero_division=0)
        f1 = f1_score(y_val, y_pred, zero_division=0)
        
        approval_rate = (tn + fn) / total_transactions
        block_rate = (tp + fp) / total_transactions
        review_rate = block_rate # Assuming we review all blocks
        
        results.append({
            "threshold": threshold,
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "approval_rate": float(approval_rate),
            "review_rate": float(review_rate),
            "block_rate": float(block_rate),
            "total_cost": float(total_cost)
        })

    results_df = pd.DataFrame(results)
    optimal_idx = results_df["total_cost"].idxmin()
    optimal_threshold = results_df.loc[optimal_idx, "threshold"]
    min_cost = results_df.loc[optimal_idx, "total_cost"]
    
    logger.info(f"Optimal threshold found: {optimal_threshold:.2f} with total cost: {min_cost:.2f}")
    
    return ThresholdResult(
        optimal_threshold=float(optimal_threshold),
        min_cost=float(min_cost),
        evaluated_thresholds=results_df
    )

if __name__ == "__main__":
    # Runnable as script for testing
    import sys
    print("Threshold optimizer can be imported and used.")
    sys.exit(0)

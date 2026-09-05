import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss

logger = logging.getLogger(__name__)

def calibrate_model(model: Any, X_val: pd.DataFrame, y_val: pd.Series, method: str = 'isotonic') -> CalibratedClassifierCV:
    """
    Calibrates a classifier using isotonic regression or sigmoid method.
    """
    logger.info(f"Calibrating model using {method} method...")
    # Wrap model with calibration
    calibrated = CalibratedClassifierCV(model, method=method, cv="prefit")
    calibrated.fit(X_val, y_val)
    logger.info("Calibration completed.")
    return calibrated

def evaluate_calibration(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluates the calibration of a model.
    """
    if hasattr(model, 'predict_proba'):
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    else:
        raise ValueError("Model must have predict_proba method for calibration evaluation.")
        
    brier = float(brier_score_loss(y_test, y_pred_proba))
    
    metrics = {
        "brier_score": brier
    }
    logger.info(f"Calibration metrics: {metrics}")
    
    return metrics

import numpy as np
from typing import List, Dict, Any, Union

class DriftDetector:
    def __init__(self, psi_threshold: float = 0.2):
        self.psi_threshold = psi_threshold

    def compute_psi(self, reference_distribution: np.ndarray, current_distribution: np.ndarray, bins: int = 10) -> float:
        if len(reference_distribution) == 0 or len(current_distribution) == 0:
            return 0.0

        min_val = min(np.min(reference_distribution), np.min(current_distribution))
        max_val = max(np.max(reference_distribution), np.max(current_distribution))
        
        if min_val == max_val:
            return 0.0

        bins_edges = np.linspace(min_val, max_val, bins + 1)
        
        ref_hist, _ = np.histogram(reference_distribution, bins=bins_edges)
        cur_hist, _ = np.histogram(current_distribution, bins=bins_edges)
        
        # Add a small epsilon to avoid division by zero
        epsilon = 0.0001
        ref_hist = (ref_hist + epsilon) / (len(reference_distribution) + bins * epsilon)
        cur_hist = (cur_hist + epsilon) / (len(current_distribution) + bins * epsilon)
        
        psi_values = (cur_hist - ref_hist) * np.log(cur_hist / ref_hist)
        return float(np.sum(psi_values))

    def check_feature_drift(self, feature_name: str, reference_values: Union[List[float], np.ndarray], current_values: Union[List[float], np.ndarray]) -> Dict[str, Any]:
        ref_arr = np.array(reference_values)
        cur_arr = np.array(current_values)
        
        psi = self.compute_psi(ref_arr, cur_arr)
        
        return {
            "feature": feature_name,
            "psi": psi,
            "is_drifted": psi >= self.psi_threshold,
            "threshold": self.psi_threshold
        }

    def check_prediction_drift(self, reference_predictions: Union[List[float], np.ndarray], current_predictions: Union[List[float], np.ndarray]) -> Dict[str, Any]:
        return self.check_feature_drift("model_predictions", reference_predictions, current_predictions)

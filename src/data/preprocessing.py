import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def apply_preprocessing(df: pd.DataFrame, scaler_path: Path, is_train: bool = False) -> pd.DataFrame:
    """Apply standard preprocessing to features. Fit scaler on train only."""
    df_clean = df.copy()
    
    # Features to scale (assuming we want to scale V1-V28 and any engineered features, 
    # but not Time, Class, or log_amount itself, though scaling log_amount is fine)
    # Let's dynamically find features to scale: numerical columns excluding Time and Class
    cols_to_scale = [c for c in df_clean.columns if c not in ['Time', 'Class']]
    
    if is_train:
        scaler = StandardScaler()
        df_clean[cols_to_scale] = scaler.fit_transform(df_clean[cols_to_scale])
        joblib.dump(scaler, scaler_path)
        logger.info(f"Fitted and saved scaler to {scaler_path}")
    else:
        if not scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found at {scaler_path}")
        scaler = joblib.load(scaler_path)
        df_clean[cols_to_scale] = scaler.transform(df_clean[cols_to_scale])
        logger.info(f"Loaded and applied scaler from {scaler_path}")
        
    return df_clean

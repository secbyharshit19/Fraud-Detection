import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, List

logger = logging.getLogger(__name__)

def compute_train_stats(df_train: pd.DataFrame) -> Dict[str, float]:
    """Compute statistics from training data for feature engineering."""
    return {
        'global_mean': df_train['Amount'].mean(),
        'global_std': df_train['Amount'].std()
    }

def engineer_features(df: pd.DataFrame, train_stats: Dict[str, float]) -> pd.DataFrame:
    """
    Engineer features safely, without target leakage.
    Velocity features are computed globally (not grouped by Class or any ID, as ID is missing).
    """
    df_feat = df.copy()
    
    # Time based features
    df_feat['hour'] = (df_feat['Time'] // 3600) % 24
    df_feat['dayofweek'] = (df_feat['Time'] // (3600 * 24)) % 7
    df_feat['is_weekend'] = (df_feat['dayofweek'] >= 5).astype(int)
    df_feat['is_night'] = ((df_feat['hour'] >= 22) | (df_feat['hour'] <= 5)).astype(int)
    
    # Amount based features
    df_feat['log_amount'] = np.log1p(df_feat['Amount'])
    df_feat['amount_zscore'] = (df_feat['Amount'] - train_stats['global_mean']) / train_stats['global_std']
    
    # Velocity features (Global)
    # Must sort by Time first
    df_feat = df_feat.sort_values('Time').reset_index(drop=True)
    
    # Convert Time to timedelta for rolling
    df_feat['Time_td'] = pd.to_timedelta(df_feat['Time'], unit='s')
    df_temp = df_feat.set_index('Time_td')
    
    df_feat['transaction_count_1h'] = df_temp['Amount'].rolling('1h').count().values
    df_feat['transaction_count_24h'] = df_temp['Amount'].rolling('24h').count().values
    df_feat['amount_sum_1h'] = df_temp['Amount'].rolling('1h').sum().values
    df_feat['amount_sum_24h'] = df_temp['Amount'].rolling('24h').sum().values
    df_feat['amount_mean_1h'] = df_temp['Amount'].rolling('1h').mean().values
    
    df_feat['time_since_prev'] = df_feat['Time'].diff().fillna(0)
    
    # Risk score (mock score using velocity and amount, without Class)
    # Just a simple combination
    risk_components = df_feat['amount_zscore'] + (df_feat['transaction_count_1h'] / 10.0)
    df_feat['risk_score'] = (risk_components - risk_components.min()) / (risk_components.max() - risk_components.min() + 1e-6)
    
    # Clean up temp cols
    df_feat = df_feat.drop(columns=['Time_td'], errors='ignore')
    
    logger.info("Feature engineering complete")
    return df_feat

def get_feature_names(df: pd.DataFrame) -> List[str]:
    """Get list of features for training (excluding Time, Class)"""
    return [c for c in df.columns if c not in ['Time', 'Class']]

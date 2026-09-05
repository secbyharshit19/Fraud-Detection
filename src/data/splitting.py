import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def temporal_split(df: pd.DataFrame, train_ratio: float=0.7, val_ratio: float=0.15, test_ratio: float=0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Chronological split sorting by Time."""
    df_sorted = df.sort_values('Time').reset_index(drop=True)
    n = len(df_sorted)
    
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    train = df_sorted.iloc[:train_end]
    val = df_sorted.iloc[train_end:val_end]
    test = df_sorted.iloc[val_end:]
    
    logger.info(f"Temporal Split - Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    if 'Class' in df.columns:
        logger.info(f"Fraud rates - Train: {train['Class'].mean():.4f}, Val: {val['Class'].mean():.4f}, Test: {test['Class'].mean():.4f}")
        
    return train, val, test

def stratified_split(df: pd.DataFrame, train_ratio: float=0.7, val_ratio: float=0.15, test_ratio: float=0.15, random_state: int=42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified split maintaining Class distribution."""
    if 'Class' not in df.columns:
        raise ValueError("Class column required for stratified split")
        
    sss1 = StratifiedShuffleSplit(n_splits=1, test_size=(1.0 - train_ratio), random_state=random_state)
    for train_idx, temp_idx in sss1.split(df, df['Class']):
        train = df.iloc[train_idx]
        temp = df.iloc[temp_idx]
        
    val_prop = val_ratio / (val_ratio + test_ratio)
    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=(1.0 - val_prop), random_state=random_state)
    for val_idx, test_idx in sss2.split(temp, temp['Class']):
        val = temp.iloc[val_idx]
        test = temp.iloc[test_idx]
        
    logger.info(f"Stratified Split - Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    logger.info(f"Fraud rates - Train: {train['Class'].mean():.4f}, Val: {val['Class'].mean():.4f}, Test: {test['Class'].mean():.4f}")
    
    return train, val, test

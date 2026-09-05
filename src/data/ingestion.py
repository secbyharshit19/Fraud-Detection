import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

def load_raw_data(filepath: Path) -> pd.DataFrame:
    """Load raw creditcard data with validation."""
    logger.info(f"Loading data from {filepath}")
    
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found at {filepath}")
        
    df = pd.read_csv(filepath)
    
    expected_cols = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount', 'Class']
    missing_cols = set(expected_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing expected columns: {missing_cols}")
        
    logger.info(f"Data loaded successfully. Shape: {df.shape}")
    logger.info(f"Fraud rate: {df['Class'].mean() * 100:.4f}%")
    logger.info(f"Total nulls: {df.isnull().sum().sum()}")
    
    return df

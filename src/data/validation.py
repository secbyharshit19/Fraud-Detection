import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def validate_data(df: pd.DataFrame) -> dict:
    """Validate data schema, values, and constraints."""
    report = {}
    
    # Check nulls
    nulls = df.isnull().sum().sum()
    report['null_count'] = int(nulls)
    
    # Check inf
    infs = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
    report['inf_count'] = int(infs)
    
    # Check amount range
    if 'Amount' in df.columns:
        neg_amounts = (df['Amount'] < 0).sum()
        report['negative_amounts'] = int(neg_amounts)
        if neg_amounts > 0:
            logger.warning(f"Found {neg_amounts} negative amounts")
            
    # Check class values
    if 'Class' in df.columns:
        invalid_classes = (~df['Class'].isin([0, 1])).sum()
        report['invalid_classes'] = int(invalid_classes)
        if invalid_classes > 0:
            logger.warning(f"Found {invalid_classes} invalid class values")
            
    # Check duplicates
    dupes = df.duplicated().sum()
    report['duplicate_count'] = int(dupes)
    
    logger.info(f"Validation report: {report}")
    return report

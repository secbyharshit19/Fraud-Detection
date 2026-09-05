import os
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config.settings import RAW_DATA_PATH, PROCESSED_DATA_DIR, ARTIFACTS_DIR
from src.data.ingestion import load_raw_data
from src.data.validation import validate_data
from src.data.feature_engineering import compute_train_stats, engineer_features, get_feature_names
from src.data.splitting import temporal_split, stratified_split
from src.data.preprocessing import apply_preprocessing
from src.data.dataset import create_training_metadata, save_dataset_metadata

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    logger.info("Starting Data Pipeline...")
    
    # 1. Ingest
    df = load_raw_data(RAW_DATA_PATH)
    
    # 2. Validate
    validate_data(df)
    
    # 3. Split (Temporal)
    logger.info("Performing Temporal Split...")
    train_df, val_df, test_df = temporal_split(df)
    
    # 4. Feature Engineering
    # Compute stats on train only
    train_stats = compute_train_stats(train_df)
    logger.info(f"Train stats: {train_stats}")
    
    logger.info("Engineering features for Train, Val, Test...")
    train_df = engineer_features(train_df, train_stats)
    val_df = engineer_features(val_df, train_stats)
    test_df = engineer_features(test_df, train_stats)
    
    # 5. Preprocess (Scale)
    scaler_path = ARTIFACTS_DIR / "scaler.pkl"
    logger.info("Scaling features...")
    train_df = apply_preprocessing(train_df, scaler_path, is_train=True)
    val_df = apply_preprocessing(val_df, scaler_path, is_train=False)
    test_df = apply_preprocessing(test_df, scaler_path, is_train=False)
    
    # 6. Save Processed Data
    logger.info("Saving processed datasets...")
    train_df.to_parquet(PROCESSED_DATA_DIR / "train.parquet")
    val_df.to_parquet(PROCESSED_DATA_DIR / "val.parquet")
    test_df.to_parquet(PROCESSED_DATA_DIR / "test.parquet")
    
    # 7. Save Metadata
    logger.info("Saving metadata...")
    stats = {
        'train_size': len(train_df),
        'val_size': len(val_df),
        'test_size': len(test_df),
        'features': get_feature_names(train_df)
    }
    metadata = create_training_metadata("v1.0", "temporal", stats)
    save_dataset_metadata(metadata, ARTIFACTS_DIR / "dataset_metadata.json")
    
    logger.info("Data Pipeline Complete!")

if __name__ == "__main__":
    run()

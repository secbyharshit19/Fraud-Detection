import logging
import os
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_root))

import pandas as pd

from src.data.feature_engineering import compute_train_stats, engineer_features, get_feature_names
from src.data.splitting import temporal_split
from src.data.preprocessing import apply_preprocessing
from src.ml.train_xgboost import train_model as train_xgb
from src.ml.train_lightgbm import train_model as train_lgb
from src.ml.train_random_forest import train_model as train_rf
from src.ml.train_isolation_forest import train_model as train_iso
from src.ml.evaluate import compare_models, evaluate_binary_classifier, print_evaluation_report
from src.ml.threshold_optimizer import optimize_threshold
from src.ml.model_registry import ModelRegistry
from src.ml.calibrate import calibrate_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    repo_root = Path(__file__).resolve().parent.parent
    raw_data_path = repo_root / "data" / "creditcard.csv"
    processed_dir = repo_root / "data" / "processed"
    models_dir = repo_root / "models" / "trained"
    artifacts_dir = repo_root / "artifacts"
    
    for d in [processed_dir, models_dir, artifacts_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    scaler_path = artifacts_dir / "scaler.pkl"

    # 1. Load Data & Data Pipeline
    logger.info("Loading raw data...")
    if not raw_data_path.exists():
        logger.error(f"Raw data not found at {raw_data_path}")
        return
        
    df = pd.read_csv(raw_data_path)
    
    logger.info("Splitting data (temporal)...")
    train_df, val_df, test_df = temporal_split(df)
    
    logger.info("Computing train stats and engineering features...")
    train_stats = compute_train_stats(train_df)
    
    train_feat = engineer_features(train_df, train_stats)
    val_feat = engineer_features(val_df, train_stats)
    test_feat = engineer_features(test_df, train_stats)
    
    logger.info("Scaling features...")
    train_scaled = apply_preprocessing(train_feat, scaler_path, is_train=True)
    val_scaled = apply_preprocessing(val_feat, scaler_path, is_train=False)
    test_scaled = apply_preprocessing(test_feat, scaler_path, is_train=False)
    
    # Save processed data for individual scripts
    train_scaled.drop(columns=['Class', 'Time']).to_parquet(processed_dir / "X_train_scaled.parquet")
    train_scaled[['Class']].to_parquet(processed_dir / "y_train.parquet")
    
    test_scaled.drop(columns=['Class', 'Time']).to_parquet(processed_dir / "X_test_scaled.parquet")
    test_scaled[['Class']].to_parquet(processed_dir / "y_test.parquet")
    
    feature_cols = [c for c in train_scaled.columns if c not in ['Time', 'Class']]
    X_train = train_scaled[feature_cols]
    y_train = train_scaled['Class']
    X_val = val_scaled[feature_cols]
    y_val = val_scaled['Class']
    X_test = test_scaled[feature_cols]
    y_test = test_scaled['Class']
    
    # 2. Train Models
    models = {}
    
    # XGBoost
    xgb_params = {
        "n_estimators": 500,
        "max_depth": 8,
        "learning_rate": 0.05,
        "min_child_weight": 5,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "scale_pos_weight": "auto-computed"
    }
    models["xgboost"] = train_xgb(X_train, y_train, xgb_params)
    
    # LightGBM
    lgb_params = {
        "n_estimators": 500,
        "max_depth": 8,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 20,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "is_unbalance": True
    }
    models["lightgbm"] = train_lgb(X_train, y_train, lgb_params)
    
    # RandomForest
    rf_params = {
        "n_estimators": 300,
        "max_depth": 15,
        "min_samples_split": 10,
        "min_samples_leaf": 5,
        "class_weight": "balanced_subsample",
        "max_features": "sqrt"
    }
    models["random_forest"] = train_rf(X_train, y_train, rf_params)
    
    # IsolationForest
    iso_params = {
        "n_estimators": 200,
        "contamination": 0.002,
        "max_features": 0.8
    }
    models["isolation_forest"] = train_iso(X_train, iso_params)
    
    # 3. Evaluate & Optimize
    registry = ModelRegistry()
    best_cost = float('inf')
    best_model_name = None
    
    for name, model in models.items():
        metrics = evaluate_binary_classifier(model, X_test, y_test, name)
        print_evaluation_report(metrics, name)
        
        # Optimize threshold on validation set
        threshold_result = optimize_threshold(model, X_val, y_val)
        
        # Save model
        import joblib
        model_path = models_dir / f"{name}_v1.pkl"
        joblib.dump(model, model_path)
        
        # Register model
        registry.register_model(
            name=name,
            version="v1",
            algorithm=name,
            features=feature_cols,
            metrics=metrics,
            threshold=threshold_result.optimal_threshold,
            artifact_path=str(model_path),
            status="TRAINING"
        )
        
        if threshold_result.min_cost < best_cost:
            best_cost = threshold_result.min_cost
            best_model_name = name

    # 4. Compare Models
    compare_models(models, X_test, y_test)
    
    logger.info(f"Pipeline complete. Best model by business cost: {best_model_name}")
    
    # Promote best model to STAGING
    if best_model_name:
        registry.promote_model(best_model_name, "v1", "STAGING")
        logger.info(f"Promoted {best_model_name}_v1 to STAGING.")

if __name__ == "__main__":
    main()

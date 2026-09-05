# Model Versioning Strategy

This document outlines the model versioning, naming conventions, and promotion workflow for the Payment Processing & Fraud Detection Platform.

## Naming Conventions
Models are identified by a combination of their algorithm and a version tag.
Format: `<algorithm>_<version>`
Example: `xgboost_v1`, `lightgbm_v2`

## Promotion Workflow
The model lifecycle consists of four states, managed via `src/ml/model_registry.py`.

1. **TRAINING**: Model is actively being trained or has finished training. Baseline evaluation is performed.
2. **VALIDATION**: Model is undergoing extended testing, threshold optimization, and calibration.
3. **STAGING**: Model is integrated with the prediction engine in a shadow-mode or staging environment. Predictions are logged but do not impact live transactions.
4. **PRODUCTION**: Model is actively serving predictions for live transactions. Only ONE model per algorithm (or one global model) can be in PRODUCTION at a given time.

### Promoting a Model
Use `ModelRegistry.promote_model(name, version, new_status)`. Promoting a model to `PRODUCTION` automatically demotes the existing production model to `ARCHIVED`.

## Artifact Storage
- **Models**: Saved as joblib `.pkl` files in `models/trained/`.
- **Registry**: Stored in `models/registry/registry.json`.
- **Training Metadata**: Saved in `artifacts/training_runs/`.

## Feature Version Tracking
Features used by a specific model are stored in the registry metadata and training run artifacts. This ensures that the inference engine can fetch the correct feature sets (e.g., `feature_version="v1"`) at runtime.

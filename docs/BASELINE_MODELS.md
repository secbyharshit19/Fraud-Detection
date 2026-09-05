# Baseline Models Documentation

**Date Preserved:** 2026-09-04  
**Source Repository:** [VeedhiBhanushali/fraud-detection-system](https://github.com/VeedhiBhanushali/fraud-detection-system)

> [!CAUTION]
> All baseline models were trained with **target-leaked features** (`txns_last_24h`, `amount_last_24h` computed via `groupby('Class')`). Their reported metrics are **invalid** and should not be cited as genuine performance. They are preserved solely for comparison and audit purposes.

---

## 1. Original XGBoost Model

| Property | Value |
|----------|-------|
| **File** | `models/baseline/original_xgb_model.pkl` |
| **Original Path** | `src/xgb_model.pkl` |
| **Algorithm** | XGBoost `Booster` (native API) |
| **Training Features** | `Amount`, `hour`, `risk_score` (3 features) |
| **Preprocessing** | StandardScaler (z-score normalization, fitted on full dataset pre-split) |
| **Class Balancing** | Unknown (no training notebook for XGBoost found) |
| **Threshold** | 0.5 (hardcoded in `kafka_consumer.py` and `aws_lambda.py`) |
| **File Size** | 454 KB |
| **Prediction API** | `xgb.DMatrix` → `.predict()` (returns probabilities) |

### Limitations
- `risk_score = Amount * (hour + 1) / (txns_last_24h + 1)` contains **derivative target leakage** via `txns_last_24h`
- Scaler was never persisted — production code sends unscaled values
- Feature name case inconsistency (`amount` vs `Amount`) across services
- Uses 3 features vs LightGBM's 6 features — different input schema

### Compatibility Issues
- XGBoost `Booster` object (not sklearn wrapper) — requires `xgb.DMatrix` for prediction
- Must use `model.predict(dmatrix)` not `model.predict(df)`
- Version-sensitive: trained on unknown XGBoost version

---

## 2. Original LightGBM Model

| Property | Value |
|----------|-------|
| **File** | `models/baseline/original_lightgbm_model.pkl` |
| **Original Path** | `src/fraud_detection_model.pkl` |
| **Algorithm** | LightGBM `LGBMClassifier` (sklearn API) |
| **Training Features** | `Amount`, `hour`, `dayofweek`, `txns_last_24h`, `amount_last_24h`, `risk_score` (6 features) |
| **Number of Estimators** | 1,000 |
| **Max Depth** | 12 |
| **Learning Rate** | 0.05 |
| **Num Leaves** | 50 |
| **Min Child Samples** | 1 |
| **Min Data in Leaf** | 1 |
| **Regularization** | `reg_alpha=0`, `reg_lambda=0` (none) |
| **Column/Row Subsampling** | `colsample_bytree=1.0`, `subsample=1.0` (none) |
| **Class Balancing** | ADASYN (`n_neighbors=5`, `random_state=42`) |
| **Preprocessing** | StandardScaler (fitted on full dataset pre-split) |
| **Threshold** | 0.5 (implicit via `model.predict()`) |
| **File Size** | 534 KB |

### Reported Metrics (INVALID — target leakage)
| Metric | Value |
|--------|-------|
| Precision | 1.000 |
| Recall | 0.935 |
| F1-Score | 0.966 |
| Accuracy | 1.000 |

### Limitations
- **Target leakage:** `txns_last_24h` and `amount_last_24h` directly leak `Class` via `groupby('Class')`
- **No regularization:** `reg_alpha=0`, `reg_lambda=0`, `min_child_samples=1` → high overfitting risk
- **No subsampling:** `colsample_bytree=1.0`, `subsample=1.0` → no regularization via sampling
- **Pre-split scaling leakage:** Test statistics leak into training scaler
- **Scaler not persisted:** API sends raw values to a model trained on z-scored data
- **ADASYN on leaked features:** Oversampling amplifies the leaked signal

### Compatibility Issues
- Trained with `lightgbm==4.6.0`
- Uses sklearn API (`predict()`, `predict_proba()`)
- Serialized with `joblib`

---

## 3. Original Random Forest Model

| Property | Value |
|----------|-------|
| **File** | `models/baseline/original_random_forest_model.pkl` |
| **Original Path** | `src/rf_model.pkl` |
| **Algorithm** | scikit-learn `RandomForestClassifier` |
| **Training Features** | Unknown (not referenced in any source file) |
| **File Size** | 13.7 MB |
| **Status** | **ORPHANED** — not used in any API, consumer, or service |

### Limitations
- No training code found in notebooks or scripts
- Feature schema unknown — cannot safely evaluate
- Large file size suggests many deep trees
- Likely trained on same leaked features as LightGBM

### Compatibility Issues
- scikit-learn version dependency unknown
- May fail to load on different sklearn versions

---

## 4. Original Isolation Forest Model

| Property | Value |
|----------|-------|
| **File** | `models/baseline/original_isolation_forest_model.pkl` |
| **Original Path** | `src/isolation_model.pkl` |
| **Algorithm** | scikit-learn `IsolationForest` |
| **Training Features** | Unknown (not referenced in any source file) |
| **File Size** | 760 KB |
| **Status** | **ORPHANED** — not used in any API, consumer, or service |

### Limitations
- Unsupervised model — does not use Class labels directly
- Training code found only in git commit history, not in current notebooks
- Feature schema unknown
- May still be indirectly contaminated if trained on preprocessed data with leaked features

### Compatibility Issues
- scikit-learn version dependency unknown
- `IsolationForest` uses `decision_function()` / `predict()` (returns -1/1), not `predict_proba()`

---

## 5. Feature Inconsistency Summary

| Model | Feature Set | Count | Leakage |
|-------|------------|-------|---------|
| XGBoost | `Amount`, `hour`, `risk_score` | 3 | `risk_score` has derivative leakage |
| LightGBM | `Amount`, `hour`, `dayofweek`, `txns_last_24h`, `amount_last_24h`, `risk_score` | 6 | `txns_last_24h`, `amount_last_24h` have direct leakage; `risk_score` has derivative leakage |
| Random Forest | Unknown | ? | Likely leaked |
| Isolation Forest | Unknown | ? | Possibly contaminated |

**These models are NOT equivalent and cannot be used interchangeably.** The new platform will train all models on a unified, leakage-free feature set.

# Data Leakage Audit

This document tracks identified data leakage issues from the original Kaggle implementation and their resolutions.

## 1. Target Leakage via Groupby ('Class')
- **Issue**: Features like `txns_last_24h` and `amount_last_24h` were computed using `groupby('Class')`. This means the feature for a transaction was computed using knowledge of whether other transactions in the window were fraud or not.
- **Why it's leakage**: In production, the `Class` is unknown at prediction time.
- **Fix**: Removed `groupby('Class')`. Velocity features are now computed across all transactions globally, sorted by `Time`.

## 2. Risk Score Derivative Leakage
- **Issue**: Risk score was previously derived using target information or features that had target leakage.
- **Why it's leakage**: Indirectly exposes the target to the model.
- **Fix**: Computed risk score using only normalized combinations of `amount_zscore`, velocity indicators, and time features, without any reference to `Class`.

## 3. Pre-split StandardScaler
- **Issue**: `StandardScaler` was fit on the entire dataset before splitting.
- **Why it's leakage**: Mean and variance of the test set influence the scaling of the training set.
- **Fix**: Fit `StandardScaler` only on the training set, and use it to transform validation and test sets.

## 4. Random Splitting of Time Series
- **Issue**: Splitting the dataset randomly ignoring the `Time` column.
- **Why it's problematic**: Future information could be used to predict past events, ignoring temporal dynamics of fraud.
- **Fix**: Implemented temporal splitting chronologically based on `Time`. (Stratified splitting is kept as an option for comparison but temporal is preferred).

## 5. Scaler Not Persisted
- **Issue**: The fitted scaler was not saved for inference.
- **Production Implication**: Inference time features cannot be scaled identically to training, causing distribution shifts and model degradation.
- **Fix**: Persist the fitted `StandardScaler` using `joblib` during the training pipeline and load it during validation/inference.

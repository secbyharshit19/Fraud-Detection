# Model Evaluation Documentation

This document outlines the evaluation methodology and metrics for the Payment Processing & Fraud Detection Platform models.

## Evaluation Methodology

Our evaluation strategy prioritizes business metrics over raw statistical measures. Fraud detection is highly imbalanced, meaning traditional accuracy is misleading.

### Key Metrics
- **ROC AUC**: Evaluates the model's ability to rank fraud above legitimate transactions.
- **PR AUC**: Precision-Recall Area Under Curve. Extremely important for highly imbalanced datasets.
- **Precision**: When the model flags a transaction as fraud, how often is it actually fraud? (Impacts False Positive cost and analyst review time)
- **Recall**: Out of all actual fraud, how much did we catch? (Impacts fraud loss)

### Threshold Optimization
The decision threshold is chosen to minimize total business cost:
`Cost = (False Negatives × Fraud Loss) + (False Positives × False Positive Cost) + (Reviews × Review Cost)`

## Baseline Models

### XGBoost v1
- **ROC AUC**: [PLACEHOLDER]
- **PR AUC**: [PLACEHOLDER]
- **Precision**: [PLACEHOLDER]
- **Recall**: [PLACEHOLDER]
- **F1 Score**: [PLACEHOLDER]
- **Optimal Threshold**: [PLACEHOLDER]

### LightGBM v1
- **ROC AUC**: [PLACEHOLDER]
- **PR AUC**: [PLACEHOLDER]
- **Precision**: [PLACEHOLDER]
- **Recall**: [PLACEHOLDER]
- **F1 Score**: [PLACEHOLDER]
- **Optimal Threshold**: [PLACEHOLDER]

### Random Forest v1
- **ROC AUC**: [PLACEHOLDER]
- **PR AUC**: [PLACEHOLDER]
- **Precision**: [PLACEHOLDER]
- **Recall**: [PLACEHOLDER]
- **F1 Score**: [PLACEHOLDER]
- **Optimal Threshold**: [PLACEHOLDER]

### Isolation Forest v1 (Unsupervised)
- **ROC AUC**: [PLACEHOLDER]
- **PR AUC**: [PLACEHOLDER]
- **Precision**: [PLACEHOLDER]
- **Recall**: [PLACEHOLDER]
- **F1 Score**: [PLACEHOLDER]
- **Optimal Threshold**: [PLACEHOLDER]

## Model Comparison
See `reports/model_comparison.csv` for detailed test set metrics and `reports/auc_comparison.png` for visual comparison.

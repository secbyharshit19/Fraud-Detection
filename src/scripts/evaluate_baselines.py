import pandas as pd
import numpy as np
import xgboost as xgb
import joblib

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score
)

# --------------------------------------------------
# Load test data
# --------------------------------------------------

test_df = pd.read_csv("data/test_processed_transactions.csv")

print("Test shape:", test_df.shape)
print("\nClass distribution:")
print(test_df["Class"].value_counts())

# --------------------------------------------------
# ORIGINAL XGBOOST
# --------------------------------------------------

print("\n" + "=" * 60)
print("ORIGINAL XGBOOST BASELINE")
print("=" * 60)

xgb_model = joblib.load("src/xgb_model.pkl")

xgb_features = [
    "Amount",
    "hour",
    "risk_score"
]

X_test_xgb = test_df[xgb_features]
y_test = test_df["Class"]

dmatrix = xgb.DMatrix(
    X_test_xgb,
    feature_names=xgb_features
)

xgb_probability = xgb_model.predict(dmatrix)

print("\nRaw prediction sample:")
print(xgb_probability[:10])

# Check probability range
print("\nProbability range:")
print(
    "min =", xgb_probability.min(),
    "max =", xgb_probability.max()
)

# --------------------------------------------------
# Determine threshold
# --------------------------------------------------

threshold = 0.5

xgb_prediction = (
    xgb_probability >= threshold
).astype(int)

# --------------------------------------------------
# Metrics
# --------------------------------------------------

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, xgb_prediction))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        xgb_prediction,
        zero_division=0
    )
)

print("\nPrecision:")
print(precision_score(
    y_test,
    xgb_prediction,
    zero_division=0
))

print("\nRecall:")
print(recall_score(
    y_test,
    xgb_prediction,
    zero_division=0
))

print("\nF1:")
print(f1_score(
    y_test,
    xgb_prediction,
    zero_division=0
))

print("\nROC-AUC:")
print(
    roc_auc_score(
        y_test,
        xgb_probability
    )
)

print("\nPR-AUC:")
print(
    average_precision_score(
        y_test,
        xgb_probability
    )
)
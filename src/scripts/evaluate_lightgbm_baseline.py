import joblib
import pandas as pd
import numpy as np

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    roc_auc_score,
    average_precision_score,
)


MODEL_PATH = "src/fraud_detection_model.pkl"
TEST_PATH = "data/test_processed_transactions.csv"

FEATURES = [
    "Amount",
    "hour",
    "dayofweek",
    "txns_last_24h",
    "amount_last_24h",
    "risk_score",
]

TARGET = "Class"

CHUNK_SIZE = 1000


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING TEST DATA")
print("=" * 60)

test_df = pd.read_csv(TEST_PATH)

print(f"Test shape: {test_df.shape}")

print("\nClass distribution:")
print(test_df[TARGET].value_counts())


# ============================================================
# PREPARE DATA
# ============================================================

missing_features = [
    feature for feature in FEATURES
    if feature not in test_df.columns
]

if missing_features:
    raise ValueError(
        f"Missing features: {missing_features}"
    )

X_test = test_df[FEATURES].copy()
y_test = test_df[TARGET].copy()


# Force clean numeric NumPy matrix
X_array = X_test.to_numpy(dtype=np.float64)


# ============================================================
# LOAD MODEL
# ============================================================

print("\n" + "=" * 60)
print("LOADING ORIGINAL LIGHTGBM MODEL")
print("=" * 60)

model = joblib.load(MODEL_PATH)

print("Model type:")
print(type(model))

print("\nModel:")
print(model)

print("\nModel features:")
print(model.feature_name_)


# ============================================================
# CHUNKED PREDICTION
# ============================================================

print("\n" + "=" * 60)
print("GENERATING CHUNKED PREDICTIONS")
print("=" * 60)

probabilities = []

total_rows = len(X_array)

for start in range(0, total_rows, CHUNK_SIZE):

    end = min(start + CHUNK_SIZE, total_rows)

    chunk = X_array[start:end]

    print(
        f"Predicting rows {start} - {end - 1}"
    )

    chunk_prob = model.predict_proba(chunk)[:, 1]

    probabilities.append(chunk_prob)


y_prob = np.concatenate(probabilities)

print("\nPrediction complete.")

print(f"Number of predictions: {len(y_prob)}")


# ============================================================
# PREDICTION CHECK
# ============================================================

print("\n" + "=" * 60)
print("PROBABILITY CHECK")
print("=" * 60)

print("First 20 probabilities:")
print(y_prob[:20])

print("\nProbability range:")
print(f"min = {y_prob.min()}")
print(f"max = {y_prob.max()}")

print("\nProbability statistics:")
print(pd.Series(y_prob).describe())


# ============================================================
# THRESHOLD
# ============================================================

THRESHOLD = 0.5

y_pred = (y_prob >= THRESHOLD).astype(int)

print("\nClassification threshold:")
print(THRESHOLD)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(y_test, y_pred)

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(cm)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(
    classification_report(
        y_test,
        y_pred,
        digits=6,
        zero_division=0,
    )
)


# ============================================================
# METRICS
# ============================================================

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0,
)

accuracy = accuracy_score(
    y_test,
    y_pred,
)

roc_auc = roc_auc_score(
    y_test,
    y_prob,
)

pr_auc = average_precision_score(
    y_test,
    y_prob,
)


print("\n" + "=" * 60)
print("FINAL METRICS")
print("=" * 60)

print(f"Precision : {precision:.6f}")
print(f"Recall    : {recall:.6f}")
print(f"F1        : {f1:.6f}")
print(f"Accuracy  : {accuracy:.6f}")
print(f"ROC-AUC   : {roc_auc:.6f}")
print(f"PR-AUC    : {pr_auc:.6f}")


# ============================================================
# COUNTS
# ============================================================

tn, fp, fn, tp = cm.ravel()

print("\n" + "=" * 60)
print("DETECTION COUNTS")
print("=" * 60)

print(f"True Negatives : {tn}")
print(f"False Positives: {fp}")
print(f"False Negatives: {fn}")
print(f"True Positives : {tp}")


# ============================================================
# BUSINESS INTERPRETATION
# ============================================================

total_fraud = int(y_test.sum())

print("\n" + "=" * 60)
print("BUSINESS VIEW")
print("=" * 60)

print(f"Actual fraud       : {total_fraud}")
print(f"Fraud detected     : {tp}")
print(f"Fraud missed       : {fn}")
print(f"Legitimate flagged : {fp}")

if total_fraud > 0:
    print(
        f"Recall             : "
        f"{tp / total_fraud:.2%}"
    )

print(
    f"Flagged transactions: "
    f"{int(y_pred.sum())}"
)

print(
    f"Flag rate           : "
    f"{y_pred.mean():.2%}"
)
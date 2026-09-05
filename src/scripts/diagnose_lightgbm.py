import joblib
import pandas as pd
import numpy as np
import lightgbm
import sklearn


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


print("=" * 60)
print("ENVIRONMENT")
print("=" * 60)

print("LightGBM:", lightgbm.__version__)
print("sklearn :", sklearn.__version__)
print("numpy   :", np.__version__)


print("\n" + "=" * 60)
print("LOADING MODEL")
print("=" * 60)

model = joblib.load(MODEL_PATH)

print("Model type:", type(model))
print("Number of estimators:", model.n_estimators)

print("\nFeature names from model:")
print(model.feature_name_)


print("\n" + "=" * 60)
print("LOADING TEST DATA")
print("=" * 60)

df = pd.read_csv(TEST_PATH)

X = df[FEATURES]

print("X shape:", X.shape)
print("X dtype:")
print(X.dtypes)

print("\nFirst row:")
print(X.iloc[0])


print("\n" + "=" * 60)
print("TEST 1: SINGLE ROW")
print("=" * 60)

try:
    single = X.iloc[[0]]

    result = model.predict_proba(single)

    print("SUCCESS")
    print(result)

except Exception as e:
    print("FAILED")
    print(type(e).__name__)
    print(str(e))


print("\n" + "=" * 60)
print("TEST 2: TEN ROWS")
print("=" * 60)

try:
    small = X.iloc[:10]

    result = model.predict_proba(small)

    print("SUCCESS")
    print(result)

except Exception as e:
    print("FAILED")
    print(type(e).__name__)
    print(str(e))


print("\n" + "=" * 60)
print("TEST 3: NUMPY ARRAY")
print("=" * 60)

try:
    arr = X.iloc[:10].to_numpy(dtype=np.float64)

    print("Array shape:", arr.shape)
    print("Array dtype:", arr.dtype)

    result = model.predict_proba(arr)

    print("SUCCESS")
    print(result)

except Exception as e:
    print("FAILED")
    print(type(e).__name__)
    print(str(e))


print("\n" + "=" * 60)
print("TEST 4: BOOSTER DIRECT PREDICTION")
print("=" * 60)

try:
    booster = model.booster_

    print("Booster:", booster)
    print("Booster feature names:")
    print(booster.feature_name())

    result = booster.predict(X.iloc[:10])

    print("SUCCESS")
    print(result)

except Exception as e:
    print("FAILED")
    print(type(e).__name__)
    print(str(e))


print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
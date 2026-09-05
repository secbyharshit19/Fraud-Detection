# PROJECT AUDIT — Existing Fraud Detection System

**Audit Date:** 2026-09-04  
**Repository:** [VeedhiBhanushali/fraud-detection-system](https://github.com/VeedhiBhanushali/fraud-detection-system)  
**Auditor:** Automated audit + manual inspection  
**Branch:** `feature/payment-fraud-platform`

---

## 1. Executive Summary

The existing repository is a **Kaggle-based credit-card fraud detection project** with a FastAPI REST service, model artifacts, Kafka producer/consumer scripts, Redis caching, and a Dockerfile. While the project demonstrates a reasonable skeleton, it suffers from **catastrophic data leakage**, **inconsistent model pipelines**, **broken infrastructure integration**, **no tests**, and **misleading performance claims**.

The reported metrics (**Precision: 1.000, Recall: 0.935, F1: 0.966**) are **fraudulent artifacts of target leakage**, not genuine model performance.

---

## 2. Repository Structure

```
fraud-detection-system/
├── .git/
├── .gitattributes              # Git LFS tracking for data/*.csv
├── Dockerfile                  # Single-container build (python:3.9)
├── LICENSE                     # MIT License
├── README.md                   # Misleading documentation
├── data/
│   ├── creditcard.csv          # Raw Kaggle dataset (150.8 MB, 284,807 rows)
│   ├── train_processed_transactions.csv   # 33,312 rows (28% — NOT 70%)
│   ├── val_processed_transactions.csv     # 42,721 rows (36%)
│   └── test_processed_transactions.csv    # 42,722 rows (36%)
├── notebooks/
│   ├── 01_data_preprocessing.ipynb        # Feature engineering + splitting
│   └── 02_model_training.ipynb            # LightGBM training
├── requirements.txt            # 16 dependencies (mostly unpinned)
├── run.sh                      # macOS-only orchestration script
├── src/
│   ├── __pycache__/
│   ├── aws_lambda.py           # AWS Lambda handler (broken paths)
│   ├── fastapi_service.py      # Main API (442 lines)
│   ├── fraud_detection_model.pkl  # LightGBM model (534 KB)
│   ├── isolation_model.pkl     # Isolation Forest model — ORPHANED (760 KB)
│   ├── kafka_consumer.py       # Kafka consumer (hardcoded macOS paths)
│   ├── kafka_producer.py       # Kafka producer (streams test data)
│   ├── redis_cache.py          # Redis get/set helpers
│   ├── rf_model.pkl            # Random Forest model — ORPHANED (13.7 MB)
│   ├── xgb_model.pkl           # XGBoost Booster model (454 KB)
│   └── scripts/
│       ├── diagnose_lightgbm.py
│       ├── evaluate_baselines.py
│       ├── evaluate_lightgbm_baseline.py
│       └── inspect-model.py
├── venv/                       # Local virtual environment (committed)
```

**MISSING:**
- ❌ No `docker-compose.yml` (README references one)
- ❌ No `.env` or `.env.example`
- ❌ No `tests/` directory — zero test files
- ❌ No `__init__.py` module files
- ❌ No model registry or versioning
- ❌ No monitoring
- ❌ No CI/CD configuration

---

## 3. Existing Architecture

```
User Request
     │
     ▼
FastAPI (/predict) ──── fraud_detection_model.pkl (LightGBM, 6 features)
     │                         │
     ├── Redis Cache           │ (cache by transaction_id)
     │                         │
     └── PostgreSQL            │ (log predictions, optional)
                               │
Kafka Producer ─► Kafka ─► Kafka Consumer ──── xgb_model.pkl (XGBoost, 3 features)
     │                                              │
     │                                              └── stdout only (no persistence)
```

**Key observation:** The FastAPI service and Kafka pipeline use **different models with different features** and are **completely disconnected**. The API has zero Kafka integration despite README claims.

---

## 4. Existing Data Pipeline

### 4.1 Raw Data
- **Source:** Kaggle Credit Card Fraud Detection dataset
- **Rows:** 284,807 (492 fraud = 0.1727% fraud rate)
- **Columns:** 31 — `Time`, `V1`–`V28` (PCA components), `Amount`, `Class`
- **Note:** `V1`–`V28` are already PCA-transformed; original features are not available

### 4.2 Preprocessing (01_data_preprocessing.ipynb)

The preprocessing notebook performs:

1. **Load** `creditcard.csv`
2. **Drop NaN** (none expected)
3. **Feature Engineering:**
   - `hour = (Time // 3600) % 24`
   - `dayofweek = (Time // (3600 * 24)) % 7`
   - ⚠️ `txns_last_24h = df.groupby('Class')['Time'].transform(lambda x: x.rolling(window=86400, min_periods=1).count())`
   - ⚠️ `amount_last_24h = df.groupby('Class')['Amount'].transform(lambda x: x.rolling(window=86400, min_periods=1).sum())`
   - ⚠️ `risk_score = Amount * (hour + 1) / (txns_last_24h + 1)`
4. **Scaling:** `StandardScaler.fit_transform()` on **entire dataset** before splitting
5. **Splitting:** `train_test_split(df, test_size=0.3)` → train(70%), then `train_test_split(temp, test_size=0.5)` → val(15%), test(15%)

### 4.3 Processed Data Anomaly

| Split | Expected Rows | Actual Rows | Expected % | Actual % |
|-------|--------------|-------------|------------|----------|
| Train | 199,365 | 33,312 | 70% | **28.1%** |
| Val   | 42,721  | 42,721 | 15% | **36.0%** |
| Test  | 42,721  | 42,722 | 15% | **36.0%** |
| **Total** | **284,807** | **118,755** | **100%** | **41.7%** |

**Finding:** Only ~42% of the original dataset was preserved in the splits. The train set is **smaller** than both validation and test sets. This may be due to the notebook being run on a subset, or Git LFS truncation.

---

## 5. Critical Data Leakage Issues

### 5.1 CATASTROPHIC: Target Leakage via `groupby('Class')`

```python
df['txns_last_24h'] = df.groupby('Class')['Time'].transform(
    lambda x: x.rolling(window=86400, min_periods=1).count()
)
df['amount_last_24h'] = df.groupby('Class')['Amount'].transform(
    lambda x: x.rolling(window=86400, min_periods=1).sum()
)
```

**Why this is catastrophic:**
- `Class` IS the target label (0=legitimate, 1=fraud)
- `groupby('Class')` computes rolling statistics **within each class separately**
- Fraud transactions (492 total) have very few preceding fraud-labeled records → `txns_last_24h` is consistently small for fraud
- Legitimate transactions (284,315 total) have many preceding records → `txns_last_24h` is consistently large
- The model simply learns: "small `txns_last_24h` → fraud" — which is a tautology

**Impact:** ALL reported metrics (Precision: 1.000, Recall: 0.935, F1: 0.966) are **completely invalid**.

### 5.2 Derivative Leakage in `risk_score`

```python
df['risk_score'] = df['Amount'] * (df['hour'] + 1) / (df['txns_last_24h'] + 1)
```

Since `txns_last_24h` contains target leakage, `risk_score` inherits it. This affects **all models**, including `xgb_model.pkl` which only uses `Amount`, `hour`, `risk_score`.

### 5.3 Rolling Window Bug

```python
x.rolling(window=86400, min_periods=1).count()
```

The DataFrame uses an integer `RangeIndex`, not a `DatetimeIndex`. Therefore `window=86400` means **86,400 rows**, not 86,400 seconds (24 hours). The intended time-based rolling window doesn't work.

### 5.4 Pre-Split Scaling Leakage

`StandardScaler.fit_transform()` is applied to the **entire dataset** before `train_test_split()`. Test/validation distribution statistics leak into training data scaling parameters.

### 5.5 Scaler Not Persisted

The `StandardScaler` is never serialized to disk. In production (`fastapi_service.py`), raw unscaled values are fed directly into models trained on scaled data — guaranteed distribution mismatch.

### 5.6 Random (Non-Temporal) Splitting

`train_test_split(random_state=42)` shuffles time-series data randomly. Training rows can occur after test rows, leaking temporal patterns.

---

## 6. Existing Models

### 6.1 fraud_detection_model.pkl (LightGBM)
| Property | Value |
|----------|-------|
| **Algorithm** | LightGBM `LGBMClassifier` |
| **Features** | `Amount`, `hour`, `dayofweek`, `txns_last_24h`, `amount_last_24h`, `risk_score` (6 features) |
| **Estimators** | 1,000 |
| **Max Depth** | 12 |
| **Learning Rate** | 0.05 |
| **Num Leaves** | 50 |
| **Regularization** | `reg_alpha=0`, `reg_lambda=0` (none) |
| **Imbalance Handling** | ADASYN (applied to training data) |
| **Training Data** | Scaled with `StandardScaler` + target leakage features |
| **Used In** | `fastapi_service.py` |
| **File Size** | 534 KB |

### 6.2 xgb_model.pkl (XGBoost)
| Property | Value |
|----------|-------|
| **Algorithm** | XGBoost `Booster` (native API, not sklearn wrapper) |
| **Features** | `Amount`, `hour`, `risk_score` (3 features) |
| **Used In** | `kafka_consumer.py`, `aws_lambda.py`, evaluation scripts |
| **File Size** | 454 KB |
| **Note** | Uses `xgb.DMatrix` for prediction, not sklearn `.predict()` |

### 6.3 rf_model.pkl (Random Forest) — ORPHANED
| Property | Value |
|----------|-------|
| **Algorithm** | scikit-learn `RandomForestClassifier` |
| **Features** | Unknown (not referenced anywhere in code) |
| **Used In** | **NOWHERE** — completely orphaned |
| **File Size** | 13.7 MB |

### 6.4 isolation_model.pkl (Isolation Forest) — ORPHANED
| Property | Value |
|----------|-------|
| **Algorithm** | scikit-learn `IsolationForest` |
| **Features** | Unknown (not referenced anywhere in code) |
| **Used In** | **NOWHERE** — completely orphaned |
| **File Size** | 760 KB |

### 6.5 Model Inconsistency Matrix

| Component | Model Used | Features | Feature Count |
|-----------|-----------|----------|---------------|
| FastAPI `/predict` | LightGBM | Amount, hour, dayofweek, txns_last_24h, amount_last_24h, risk_score | 6 |
| Kafka Consumer | XGBoost | Amount, hour, risk_score | 3 |
| AWS Lambda | XGBoost | amount (lowercase!), hour, risk_score | 3 |
| Kafka Producer | N/A | amount, hour, risk_score | 3 (emits only) |

**These models are NOT interchangeable.** They use different feature sets, different algorithms, and different APIs.

---

## 7. Existing APIs

### 7.1 FastAPI Endpoints

| Method | Endpoint | Description | Issues |
|--------|---------|-------------|--------|
| `GET` | `/` | Health message | None |
| `GET` | `/health` | Model + DB status | None |
| `POST` | `/predict` | Single transaction prediction | Unscaled inputs, leaky features required |
| `POST` | `/predict/batch` | Batch prediction | Skips DB logging for cached transactions |
| `POST` | `/predict/csv` | CSV file upload prediction | No file size limit — DoS risk |
| `GET` | `/transactions` | Recent transactions from DB | Requires PostgreSQL |
| `GET` | `/stats` | Fraud statistics | Crashes on empty DB (NULL handling bug) |

### 7.2 API Schema Mismatch

**README example request:**
```json
{"amount": 5000, "location": "New York", "transaction_type": "credit", "risk_score": 0.85}
```

**Actual Pydantic schema:**
```json
{"amount": 5000.0, "hour": 14, "dayofweek": 2, "txns_last_24h": 1.0, "amount_last_24h": 5000.0, "risk_score": 0.85}
```

Sending the README's example payload to `/predict` returns **422 Unprocessable Entity**.

---

## 8. Existing Infrastructure

### 8.1 Redis
- **Implementation:** Simple get/set cache in `redis_cache.py`
- **Issues:**
  - Hardcoded `localhost:6379` with no env override
  - No socket timeouts — blocks indefinitely if Redis is down
  - No key namespacing (collision risk)
  - 1-hour TTL hardcoded
  - Cache key is `transaction_id` only — payload changes ignored

### 8.2 Kafka
- **Producer:** Reads test CSV, sends 3 fields per row to `fraud_transactions` topic with 1s delay
- **Consumer:** Loads XGBoost model via hardcoded macOS path, predictions go to stdout only
- **Issues:**
  - Hardcoded `localhost:9092` with no env override
  - Consumer has hardcoded absolute path: `/Users/veedhibhanushali/fraud-detection-system/src/xgb_model.pkl`
  - No consumer `group_id`, no `auto_offset_reset`
  - No delivery confirmation in producer (no `flush()`)
  - Predictions never persisted — logged to console only
  - No connection to FastAPI service

### 8.3 PostgreSQL
- **Implementation:** Optional connection at startup in `fastapi_service.py`
- **Issues:**
  - Single global `psycopg2` connection (NOT thread-safe for concurrent requests)
  - Never reconnects if DB is unavailable at startup
  - Default credentials: `postgres:postgres`
  - Only one table: `predictions`
  - Batch endpoint skips DB logging for cache hits

### 8.4 Docker
- **Dockerfile:** Copies `src/` and `data/` (216+ MB CSV files) into image
- **Issues:**
  - No `docker-compose.yml` exists despite README instructions
  - Port mismatch: Dockerfile=8000, run.sh=8001
  - No `EXPOSE` directive
  - Missing `libgomp1` for LightGBM on Debian
  - Python 3.9 in Docker vs potential 3.12 locally
  - 216+ MB of CSV data copied into production container

### 8.5 run.sh
- macOS-specific: hardcoded `/opt/homebrew/Cellar/kafka/...` paths
- Uses `open -a Docker` (macOS only)
- Port collision: binds port 8001 to both local uvicorn AND Docker container
- Non-functional on Windows or Linux

---

## 9. Limitations & Bugs Summary

### 9.1 Critical Bugs

| # | Component | Bug | Severity |
|---|-----------|-----|----------|
| 1 | Preprocessing | Target leakage via `groupby('Class')` | **CRITICAL** |
| 2 | Preprocessing | Pre-split scaling leaks test statistics | **CRITICAL** |
| 3 | kafka_consumer.py | Hardcoded path `/Users/veedhibhanushali/...` | **CRITICAL** |
| 4 | fastapi_service.py | Single non-threadsafe DB connection | **CRITICAL** |
| 5 | fastapi_service.py | Raw unscaled inputs to scaled model | **CRITICAL** |
| 6 | Data splits | Train=28%, Val=36%, Test=36% (broken) | **HIGH** |
| 7 | fastapi_service.py | `/stats` crashes on empty DB (NULL) | **HIGH** |
| 8 | fastapi_service.py | CORS wildcard with credentials (invalid) | **HIGH** |
| 9 | aws_lambda.py | Invalid relative path for Lambda | **HIGH** |
| 10 | aws_lambda.py | Lowercase feature names mismatch | **HIGH** |
| 11 | kafka_producer.py | No `producer.flush()` — data loss | **HIGH** |
| 12 | redis_cache.py | No timeouts — hangs on Redis failure | **HIGH** |
| 13 | fastapi_service.py | `/predict/csv` — unbounded memory read | **MEDIUM** |
| 14 | README.md | Example payload doesn't match API schema | **MEDIUM** |
| 15 | README.md | References non-existent docker-compose | **MEDIUM** |
| 16 | Port config | 8000 vs 8001 inconsistency | **MEDIUM** |

### 9.2 Security Issues

| # | Issue |
|---|-------|
| 1 | Default PostgreSQL credentials `postgres:postgres` |
| 2 | CORS `allow_origins=["*"]` with `allow_credentials=True` |
| 3 | `aws_lambda.py` exposes internal errors in HTTP response |
| 4 | No input validation beyond Pydantic type checking |
| 5 | No authentication or authorization |
| 6 | No rate limiting |
| 7 | CSV upload with no file size limit |

---

## 10. Opportunities for Improvement

### 10.1 Immediate Fixes Required
1. **Fix data leakage** — Replace `groupby('Class')` with proper entity-based or global velocity features
2. **Fix preprocessing** — Fit scaler on train only, persist scaler, apply consistently
3. **Fix data splits** — Use temporal split, proper 70/15/15 ratio
4. **Fix model consistency** — Standardize feature sets across all services
5. **Fix infrastructure** — Use connection pooling, environment variables, configurable endpoints

### 10.2 Platform Transformation
1. **Payment processing service** with proper transaction lifecycle
2. **Multi-model ensemble** with risk aggregation
3. **Rule-based fraud engine** complementing ML models
4. **Event-driven architecture** with proper Kafka integration
5. **Fraud case management** for analyst workflow
6. **Model versioning and registry**
7. **Monitoring and drift detection**
8. **Explainable AI** for fraud decisions
9. **Proper Docker Compose** with all services
10. **Comprehensive testing**

### 10.3 Data & ML Improvements
1. **Leakage-free feature engineering** with production-compatible velocity features
2. **Temporal validation** to simulate realistic deployment
3. **Threshold optimization** instead of default 0.5
4. **Model calibration** for reliable probability estimates
5. **Isolation Forest** as anomaly signal (currently orphaned)
6. **SHAP explanations** for tree-based models
7. **Proper class imbalance handling** comparison

---

## 11. Files Inventory

### Model Artifacts (to preserve as baselines)
| File | Size | Algorithm | Status |
|------|------|-----------|--------|
| `src/fraud_detection_model.pkl` | 534 KB | LightGBM | Active (FastAPI) |
| `src/xgb_model.pkl` | 454 KB | XGBoost Booster | Active (Kafka) |
| `src/rf_model.pkl` | 13.7 MB | Random Forest | Orphaned |
| `src/isolation_model.pkl` | 760 KB | Isolation Forest | Orphaned |

### Source Files
| File | Lines | Description |
|------|-------|-------------|
| `src/fastapi_service.py` | 442 | Main API service |
| `src/kafka_producer.py` | 25 | Kafka message producer |
| `src/kafka_consumer.py` | 31 | Kafka message consumer |
| `src/redis_cache.py` | 27 | Redis caching utility |
| `src/aws_lambda.py` | 31 | AWS Lambda handler |
| `src/scripts/diagnose_lightgbm.py` | 140 | LightGBM diagnostic |
| `src/scripts/evaluate_baselines.py` | 123 | XGBoost evaluation |
| `src/scripts/evaluate_lightgbm_baseline.py` | 283 | LightGBM evaluation |
| `src/scripts/inspect-model.py` | 57 | XGBoost inspection |

### Data Files
| File | Size | Rows |
|------|------|------|
| `data/creditcard.csv` | 150.8 MB | 284,807 |
| `data/train_processed_transactions.csv` | 21.4 MB | 33,312 |
| `data/val_processed_transactions.csv` | 27.5 MB | 42,721 |
| `data/test_processed_transactions.csv` | 27.5 MB | 42,722 |

---

## 12. Conclusion

The existing repository provides a useful starting skeleton with:
- ✅ A working FastAPI structure
- ✅ Multiple trained model artifacts
- ✅ Basic Redis caching pattern
- ✅ Kafka producer/consumer patterns
- ✅ PostgreSQL integration pattern
- ✅ Dockerfile

However, the project requires **fundamental reconstruction** in:
- ❌ Data pipeline (leakage, scaling, splitting)
- ❌ Model training (all metrics invalid)
- ❌ Infrastructure integration (disconnected, hardcoded, broken)
- ❌ Testing (zero tests)
- ❌ Documentation (misleading claims)
- ❌ Security (multiple vulnerabilities)
- ❌ Architecture (no payment processing, no case management, no monitoring)

**This audit will serve as the foundation for transforming the project into a Payment Processing & Fraud Detection Platform.**

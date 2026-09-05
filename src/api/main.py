"""
Payment Processing & Fraud Detection Platform — Main API Service

Production-grade API integrating payment processing, fraud detection,
case management, and monitoring.
"""
import datetime
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from src.schemas.transaction import (
    TransactionRequest,
    FraudScoreResponse,
    TriggeredRule,
)
from src.schemas.payment import PaymentStatus, PaymentResponse
from src.schemas.case import (
    CaseStatus,
    AnalystFeedbackRequest,
    FeedbackLabel,
)

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("fraud_platform")

# ─── In-memory stores (replaced by DB/Redis in production) ───────────────────
_transactions: dict = {}
_predictions: dict = {}
_cases: dict = {}
_feedback: list = []
_metrics = {
    "total_transactions": 0,
    "fraud_detected": 0,
    "blocked": 0,
    "under_review": 0,
    "approved": 0,
    "total_risk_score": 0.0,
    "total_processing_time_ms": 0.0,
    "errors": 0,
}

# ─── Model loading ───────────────────────────────────────────────────────────
_models = {}
_model_version = "fraud-v1.0"
_feature_version = "features-v1"
_rule_version = "rules-v1.0"

# Resolve project root for reliable path resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_models():
    """Load trained models at startup. Graceful fallback if missing."""
    import joblib

    model_dir = _PROJECT_ROOT / "models" / "trained"
    baseline_dir = _PROJECT_ROOT / "models" / "baseline"

    model_files = {
        "xgboost": [model_dir / "xgboost_v1.pkl", baseline_dir / "original_xgb_model.pkl"],
        "lightgbm": [model_dir / "lightgbm_v1.pkl", baseline_dir / "original_lightgbm_model.pkl"],
        "random_forest": [model_dir / "random_forest_v1.pkl", baseline_dir / "original_random_forest_model.pkl"],
        "isolation_forest": [model_dir / "isolation_forest_v1.pkl", baseline_dir / "original_isolation_forest_model.pkl"],
    }

    for name, paths in model_files.items():
        for path in paths:
            if path.exists():
                try:
                    _models[name] = joblib.load(path)
                    logger.info(f"Loaded model: {name} from {path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {name} from {path}: {e}")
        if name not in _models:
            logger.warning(f"Model {name} not available")


# ─── Rule Engine ─────────────────────────────────────────────────────────────
def _evaluate_rules(transaction: TransactionRequest) -> list:
    """Evaluate fraud rules against a transaction."""
    triggered = []

    # R001: High amount
    if transaction.amount > 5000:
        triggered.append(TriggeredRule(
            rule_id="R001", name="HIGH_AMOUNT",
            severity="HIGH",
            reason=f"Transaction amount ${transaction.amount:.2f} exceeds $5,000 threshold",
        ))

    # R002: Very high amount
    if transaction.amount > 10000:
        triggered.append(TriggeredRule(
            rule_id="R002", name="VERY_HIGH_AMOUNT",
            severity="CRITICAL",
            reason=f"Transaction amount ${transaction.amount:.2f} exceeds $10,000 threshold",
        ))

    # R004: Night + high amount
    now = transaction.timestamp or datetime.datetime.now(datetime.timezone.utc)
    hour = now.hour
    if (hour >= 22 or hour <= 5) and transaction.amount > 2000:
        triggered.append(TriggeredRule(
            rule_id="R004", name="NIGHT_HIGH_AMOUNT",
            severity="HIGH",
            reason=f"High amount ${transaction.amount:.2f} during nighttime (hour={hour})",
        ))

    # R006: Suspicious round amount
    if transaction.amount >= 1000 and transaction.amount == int(transaction.amount):
        triggered.append(TriggeredRule(
            rule_id="R006", name="SUSPICIOUS_ROUND_AMOUNT",
            severity="MEDIUM",
            reason=f"Large round amount ${transaction.amount:.2f}",
        ))

    return triggered


def _compute_risk_score(transaction: TransactionRequest, triggered_rules: list) -> tuple:
    """Compute risk score (0-100) from rules and basic heuristics."""
    reasons = []

    # Rule-based score
    rule_score = 0.0
    for rule in triggered_rules:
        if rule.severity == "CRITICAL":
            rule_score += 40
        elif rule.severity == "HIGH":
            rule_score += 25
        elif rule.severity == "MEDIUM":
            rule_score += 15
        else:
            rule_score += 5
        reasons.append(rule.reason)
    rule_score = min(rule_score, 100)

    # Amount-based heuristic
    amount_score = min(transaction.amount / 200, 100)

    # Time-based heuristic
    now = transaction.timestamp or datetime.datetime.now(datetime.timezone.utc)
    hour = now.hour
    time_score = 50 if (hour >= 22 or hour <= 5) else 10

    # Aggregate with weights
    score = 0.40 * rule_score + 0.35 * amount_score + 0.25 * time_score
    score = max(0, min(100, score))

    if not reasons:
        if score < 30:
            reasons.append("Transaction appears normal")
        elif score < 70:
            reasons.append("Moderate risk indicators detected")
        else:
            reasons.append("Multiple high-risk indicators detected")

    return round(score), reasons


def _get_decision(risk_score: int) -> str:
    """Convert risk score to decision."""
    review_threshold = int(os.getenv("RISK_THRESHOLD_REVIEW", "30"))
    block_threshold = int(os.getenv("RISK_THRESHOLD_BLOCK", "70"))
    if risk_score >= block_threshold:
        return "BLOCK"
    elif risk_score >= review_threshold:
        return "REVIEW"
    return "ALLOW"


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Payment Processing & Fraud Detection Platform")
    _load_models()
    logger.info(f"Models loaded: {list(_models.keys())}")
    yield
    logger.info("Shutting down platform")


# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Payment Processing & Fraud Detection Platform",
    description="Real-time payment processing with ML-powered fraud detection, "
                "rule engine, risk scoring, and case management.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Middleware: Request ID ──────────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Processing-Time-Ms"] = f"{elapsed:.2f}"
    return response


# ─── Health ──────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "models_loaded": list(_models.keys()),
        "model_count": len(_models),
        "model_version": _model_version,
        "transactions_processed": _metrics["total_transactions"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ─── Payments ────────────────────────────────────────────────────────────────
@app.post("/payments")
def process_payment(transaction: TransactionRequest):
    """Process a payment transaction with fraud detection."""
    start = time.time()
    transaction_id = transaction.transaction_id or str(uuid.uuid4())

    # Idempotency check
    if transaction_id in _transactions:
        return _transactions[transaction_id]

    try:
        now = datetime.datetime.now(datetime.timezone.utc)

        # Run fraud check
        triggered_rules = _evaluate_rules(transaction)
        risk_score, reasons = _compute_risk_score(transaction, triggered_rules)
        decision = _get_decision(risk_score)

        # Map decision to payment status
        status_map = {
            "ALLOW": "APPROVED",
            "REVIEW": "REVIEW",
            "BLOCK": "BLOCKED",
        }
        status = status_map.get(decision, "REVIEW")

        processing_time = (time.time() - start) * 1000

        # Store prediction
        prediction = {
            "transaction_id": transaction_id,
            "risk_score": risk_score,
            "fraud_probability": risk_score / 100.0,
            "decision": decision,
            "model_version": _model_version,
            "feature_version": _feature_version,
            "triggered_rules": [r.dict() for r in triggered_rules],
            "reasons": reasons,
            "processing_time_ms": round(processing_time, 2),
        }
        _predictions[transaction_id] = prediction

        # Store transaction — use plain dict to avoid Pydantic datetime issues
        tx_data = {
            "transaction_id": transaction_id,
            "status": status,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "risk_score": risk_score,
            "decision": decision,
            "message": f"Payment {status.lower()}",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _transactions[transaction_id] = tx_data

        # Update metrics
        _metrics["total_transactions"] += 1
        _metrics["total_risk_score"] += risk_score
        _metrics["total_processing_time_ms"] += processing_time
        if decision == "BLOCK":
            _metrics["blocked"] += 1
            _metrics["fraud_detected"] += 1
        elif decision == "REVIEW":
            _metrics["under_review"] += 1
        else:
            _metrics["approved"] += 1

        # Auto-create case for REVIEW/BLOCK
        if decision in ("REVIEW", "BLOCK"):
            case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
            case = {
                "case_id": case_id,
                "transaction_id": transaction_id,
                "risk_score": risk_score,
                "decision": decision,
                "triggered_rules": [r.dict() for r in triggered_rules],
                "model_version": _model_version,
                "explanation": {"reasons": reasons},
                "status": CaseStatus.UNDER_REVIEW.value,
                "analyst_id": None,
                "analyst_notes": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
            _cases[case_id] = case

        logger.info(
            f"Payment processed: txn={transaction_id} "
            f"risk={risk_score} decision={decision} "
            f"rules={len(triggered_rules)} time={processing_time:.1f}ms"
        )

        return tx_data

    except Exception as e:
        _metrics["errors"] += 1
        logger.error(f"Payment processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")


@app.get("/payments/{transaction_id}")
def get_payment(transaction_id: str):
    """Get payment details."""
    if transaction_id not in _transactions:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return _transactions[transaction_id]


# ─── Fraud Predictions ──────────────────────────────────────────────────────
@app.get("/fraud/predictions/{transaction_id}")
def get_fraud_prediction(transaction_id: str):
    """Get fraud prediction details."""
    if transaction_id not in _predictions:
        raise HTTPException(status_code=404, detail=f"No prediction for {transaction_id}")
    return _predictions[transaction_id]


# ─── Fraud Cases ─────────────────────────────────────────────────────────────
@app.get("/fraud/cases")
def list_cases(
    status: Optional[str] = Query(None, description="Filter by case status"),
    limit: int = Query(100, ge=1, le=500),
):
    """List fraud cases."""
    cases = list(_cases.values())
    if status:
        cases = [c for c in cases if c["status"] == status]
    return {"cases": cases[:limit], "total": len(cases)}


@app.get("/fraud/cases/{case_id}")
def get_case(case_id: str):
    """Get a specific fraud case."""
    if case_id not in _cases:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return _cases[case_id]


@app.patch("/fraud/cases/{case_id}")
def update_case(
    case_id: str,
    status: str = Query(..., description="New case status"),
    analyst_id: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
):
    """Update a fraud case status."""
    if case_id not in _cases:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    valid_statuses = [s.value for s in CaseStatus]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {valid_statuses}")

    case = _cases[case_id]
    case["status"] = status
    case["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if analyst_id:
        case["analyst_id"] = analyst_id
    if notes:
        case["analyst_notes"] = notes

    logger.info(f"Case updated: {case_id} -> {status} by {analyst_id}")
    return case


@app.post("/fraud/cases/{case_id}/feedback")
def add_feedback(case_id: str, feedback: AnalystFeedbackRequest):
    """Add analyst feedback to a fraud case."""
    if case_id not in _cases:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    case = _cases[case_id]
    feedback_entry = {
        "case_id": case_id,
        "transaction_id": case["transaction_id"],
        "label": feedback.label.value if isinstance(feedback.label, FeedbackLabel) else feedback.label,
        "analyst_id": feedback.analyst_id,
        "notes": feedback.notes,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    _feedback.append(feedback_entry)

    logger.info(f"Feedback added: case={case_id} label={feedback.label} analyst={feedback.analyst_id}")
    return {"message": "Feedback recorded", "feedback": feedback_entry}


# ─── Statistics ──────────────────────────────────────────────────────────────
@app.get("/fraud/stats")
def get_fraud_stats():
    """Get fraud detection statistics."""
    total = _metrics["total_transactions"]
    return {
        "total_transactions": total,
        "fraud_detected": _metrics["fraud_detected"],
        "fraud_rate": round((_metrics["fraud_detected"] / total * 100), 2) if total > 0 else 0,
        "blocked": _metrics["blocked"],
        "under_review": _metrics["under_review"],
        "approved": _metrics["approved"],
        "average_risk_score": round((_metrics["total_risk_score"] / total), 1) if total > 0 else 0,
        "average_processing_time_ms": round((_metrics["total_processing_time_ms"] / total), 2) if total > 0 else 0,
        "error_count": _metrics["errors"],
        "active_cases": len(_cases),
        "feedback_count": len(_feedback),
    }


# ─── Models ──────────────────────────────────────────────────────────────────
@app.get("/models")
def list_models():
    """List loaded models."""
    return {
        "models": [
            {
                "name": name,
                "version": _model_version,
                "status": "PRODUCTION",
                "type": type(model).__name__,
            }
            for name, model in _models.items()
        ],
        "total": len(_models),
    }


@app.get("/models/{model_name}")
def get_model(model_name: str):
    """Get model details."""
    if model_name not in _models:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    model = _models[model_name]
    return {
        "name": model_name,
        "version": _model_version,
        "type": type(model).__name__,
        "status": "PRODUCTION",
    }


# ─── Metrics ─────────────────────────────────────────────────────────────────
@app.get("/metrics")
def get_metrics():
    """Get platform metrics for monitoring."""
    total = _metrics["total_transactions"]
    return {
        "transactions": {
            "total": total,
            "approved": _metrics["approved"],
            "blocked": _metrics["blocked"],
            "review": _metrics["under_review"],
        },
        "fraud": {
            "detected": _metrics["fraud_detected"],
            "rate": round((_metrics["fraud_detected"] / total * 100), 2) if total > 0 else 0,
        },
        "performance": {
            "avg_risk_score": round((_metrics["total_risk_score"] / total), 2) if total > 0 else 0,
            "avg_processing_time_ms": round((_metrics["total_processing_time_ms"] / total), 2) if total > 0 else 0,
            "error_count": _metrics["errors"],
        },
        "models": {
            "loaded": list(_models.keys()),
            "version": _model_version,
        },
    }


# ─── Root ────────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    """Root endpoint."""
    return {
        "message": "Payment Processing & Fraud Detection Platform is running!",
        "version": "2.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

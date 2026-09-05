from typing import List

def get_create_tables_sql() -> List[str]:
    """Returns SQL queries to create all required tables."""
    return [
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(100) UNIQUE NOT NULL,
            customer_id VARCHAR(100) NOT NULL,
            merchant_id VARCHAR(100) NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            currency VARCHAR(3) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            risk_score NUMERIC(5, 4),
            decision VARCHAR(50),
            model_version VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS fraud_predictions (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(100) REFERENCES transactions(transaction_id),
            risk_score NUMERIC(5, 4) NOT NULL,
            fraud_probability NUMERIC(5, 4) NOT NULL,
            decision VARCHAR(50) NOT NULL,
            model_version VARCHAR(50) NOT NULL,
            feature_version VARCHAR(50) NOT NULL,
            rule_version VARCHAR(50) NOT NULL,
            triggered_rules JSONB,
            explanation JSONB,
            processing_time_ms NUMERIC(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS fraud_cases (
            id SERIAL PRIMARY KEY,
            case_id VARCHAR(100) UNIQUE NOT NULL,
            transaction_id VARCHAR(100) REFERENCES transactions(transaction_id),
            risk_score NUMERIC(5, 4) NOT NULL,
            decision VARCHAR(50) NOT NULL,
            triggered_rules JSONB,
            model_version VARCHAR(50),
            explanation JSONB,
            status VARCHAR(50) NOT NULL,
            analyst_id VARCHAR(100),
            analyst_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS analyst_feedback (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(100) REFERENCES transactions(transaction_id),
            label VARCHAR(50) NOT NULL,
            analyst_id VARCHAR(100) NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS model_versions (
            id SERIAL PRIMARY KEY,
            model_name VARCHAR(100) NOT NULL,
            version VARCHAR(50) NOT NULL UNIQUE,
            algorithm VARCHAR(100) NOT NULL,
            training_date TIMESTAMP NOT NULL,
            features JSONB NOT NULL,
            metrics JSONB NOT NULL,
            threshold NUMERIC(5, 4) NOT NULL,
            artifact_path VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            entity_type VARCHAR(100) NOT NULL,
            entity_id VARCHAR(100) NOT NULL,
            details JSONB NOT NULL,
            user_id VARCHAR(100),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """CREATE INDEX IF NOT EXISTS idx_transactions_tx_id ON transactions(transaction_id);""",
        """CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);""",
        """CREATE INDEX IF NOT EXISTS idx_transactions_merchant_id ON transactions(merchant_id);""",
        """CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);""",
        """CREATE INDEX IF NOT EXISTS idx_cases_status ON fraud_cases(status);""",
        """CREATE INDEX IF NOT EXISTS idx_cases_created_at ON fraud_cases(created_at);"""
    ]

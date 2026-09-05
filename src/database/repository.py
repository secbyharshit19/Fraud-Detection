import json
import logging
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from src.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

class TransactionRepository(BaseRepository):
    def save_transaction(self, data: Dict[str, Any]) -> Optional[str]:
        query = """
        INSERT INTO transactions (transaction_id, customer_id, merchant_id, amount, currency, timestamp, payment_method, status, risk_score, decision, model_version)
        VALUES (%(transaction_id)s, %(customer_id)s, %(merchant_id)s, %(amount)s, %(currency)s, %(timestamp)s, %(payment_method)s, %(status)s, %(risk_score)s, %(decision)s, %(model_version)s)
        RETURNING transaction_id;
        """
        with self.db.get_connection() as conn:
            if not conn:
                return None
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, data)
                    tx_id = cursor.fetchone()[0]
                conn.commit()
                return tx_id
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Error saving transaction: {e}")
                return None

    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM transactions WHERE transaction_id = %s;"
        with self.db.get_connection() as conn:
            if not conn:
                return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (transaction_id,))
                    return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
            except psycopg2.Error as e:
                logger.error(f"Error getting transaction: {e}")
                return None

    def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        query = "UPDATE transactions SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE transaction_id = %s;"
        with self.db.get_connection() as conn:
            if not conn:
                return False
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (status, transaction_id))
                conn.commit()
                return True
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Error updating transaction status: {e}")
                return False

    def list_transactions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        query = "SELECT * FROM transactions ORDER BY created_at DESC LIMIT %s OFFSET %s;"
        with self.db.get_connection() as conn:
            if not conn:
                return []
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (limit, offset))
                    return [dict(row) for row in cursor.fetchall()]
            except psycopg2.Error as e:
                logger.error(f"Error listing transactions: {e}")
                return []

class PredictionRepository(BaseRepository):
    def save_prediction(self, data: Dict[str, Any]) -> bool:
        query = """
        INSERT INTO fraud_predictions (transaction_id, risk_score, fraud_probability, decision, model_version, feature_version, rule_version, triggered_rules, explanation, processing_time_ms)
        VALUES (%(transaction_id)s, %(risk_score)s, %(fraud_probability)s, %(decision)s, %(model_version)s, %(feature_version)s, %(rule_version)s, %(triggered_rules)s, %(explanation)s, %(processing_time_ms)s);
        """
        # Ensure jsonb fields are dumped to strings
        d = data.copy()
        d['triggered_rules'] = json.dumps(d.get('triggered_rules', []))
        d['explanation'] = json.dumps(d.get('explanation', {}))
        
        with self.db.get_connection() as conn:
            if not conn:
                return False
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, d)
                conn.commit()
                return True
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Error saving prediction: {e}")
                return False

    def get_prediction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM fraud_predictions WHERE transaction_id = %s ORDER BY created_at DESC LIMIT 1;"
        with self.db.get_connection() as conn:
            if not conn:
                return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (transaction_id,))
                    return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
            except psycopg2.Error as e:
                logger.error(f"Error getting prediction: {e}")
                return None

class CaseRepository(BaseRepository):
    def create_case(self, data: Dict[str, Any]) -> Optional[str]:
        query = """
        INSERT INTO fraud_cases (case_id, transaction_id, risk_score, decision, triggered_rules, model_version, explanation, status)
        VALUES (%(case_id)s, %(transaction_id)s, %(risk_score)s, %(decision)s, %(triggered_rules)s, %(model_version)s, %(explanation)s, %(status)s)
        RETURNING case_id;
        """
        d = data.copy()
        d['triggered_rules'] = json.dumps(d.get('triggered_rules', []))
        d['explanation'] = json.dumps(d.get('explanation', {}))
        
        with self.db.get_connection() as conn:
            if not conn:
                return None
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, d)
                    case_id = cursor.fetchone()[0]
                conn.commit()
                return case_id
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Error creating case: {e}")
                return None

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM fraud_cases WHERE case_id = %s;"
        with self.db.get_connection() as conn:
            if not conn:
                return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (case_id,))
                    return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
            except psycopg2.Error as e:
                logger.error(f"Error getting case: {e}")
                return None

    def list_cases(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if status:
            query = "SELECT * FROM fraud_cases WHERE status = %s ORDER BY created_at DESC LIMIT %s;"
            params = (status, limit)
        else:
            query = "SELECT * FROM fraud_cases ORDER BY created_at DESC LIMIT %s;"
            params = (limit,)
            
        with self.db.get_connection() as conn:
            if not conn:
                return []
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
            except psycopg2.Error as e:
                logger.error(f"Error listing cases: {e}")
                return []

    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_clauses = []
        values = []
        for k, v in updates.items():
            set_clauses.append(f"{k} = %s")
            values.append(v)
        
        if not set_clauses:
            return self.get_case(case_id)
            
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE fraud_cases SET {', '.join(set_clauses)} WHERE case_id = %s RETURNING *;"
        values.append(case_id)
        
        with self.db.get_connection() as conn:
            if not conn:
                return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, tuple(values))
                    res = dict(cursor.fetchone()) if cursor.rowcount > 0 else None
                conn.commit()
                return res
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Error updating case: {e}")
                return None

class FeedbackRepository(BaseRepository):
    def save_feedback(self, data: Dict[str, Any]) -> bool:
        query = """
        INSERT INTO analyst_feedback (transaction_id, label, analyst_id, notes)
        VALUES (%(transaction_id)s, %(label)s, %(analyst_id)s, %(notes)s);
        """
        with self.db.get_connection() as conn:
            if not conn:
                return False
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, data)
                conn.commit()
                return True
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Error saving feedback: {e}")
                return False

    def get_feedback(self, transaction_id: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM analyst_feedback WHERE transaction_id = %s ORDER BY created_at DESC;"
        with self.db.get_connection() as conn:
            if not conn:
                return []
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (transaction_id,))
                    return [dict(row) for row in cursor.fetchall()]
            except psycopg2.Error as e:
                logger.error(f"Error getting feedback: {e}")
                return []

class AuditRepository(BaseRepository):
    def log_event(self, event_type: str, entity_type: str, entity_id: str, details: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        query = """
        INSERT INTO audit_logs (event_type, entity_type, entity_id, details, user_id)
        VALUES (%s, %s, %s, %s, %s);
        """
        with self.db.get_connection() as conn:
            if not conn:
                return False
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (event_type, entity_type, entity_id, json.dumps(details), user_id))
                conn.commit()
                return True
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Error logging audit event: {e}")
                return False

    def get_audit_trail(self, entity_id: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM audit_logs WHERE entity_id = %s ORDER BY timestamp DESC;"
        with self.db.get_connection() as conn:
            if not conn:
                return []
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (entity_id,))
                    return [dict(row) for row in cursor.fetchall()]
            except psycopg2.Error as e:
                logger.error(f"Error getting audit trail: {e}")
                return []

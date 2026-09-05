import logging
from contextlib import contextmanager
from typing import Generator
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from src.config.settings import DatabaseConfig
from src.database.models import get_create_tables_sql

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self._pool = None
        self._is_available = False
        try:
            self._pool = ThreadedConnectionPool(
                minconn=DatabaseConfig.MIN_CONNS,
                maxconn=DatabaseConfig.MAX_CONNS,
                host=DatabaseConfig.HOST,
                port=DatabaseConfig.PORT,
                dbname=DatabaseConfig.NAME,
                user=DatabaseConfig.USER,
                password=DatabaseConfig.PASSWORD,
                connect_timeout=2
            )
            self._is_available = True
            logger.info("Database connection pool created.")
        except psycopg2.Error as e:
            logger.warning(f"Failed to connect to database: {e}")

    @contextmanager
    def get_connection(self) -> Generator:
        if not self._is_available or not self._pool:
            yield None
            return

        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            yield None
        finally:
            if conn:
                try:
                    self._pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Failed to return connection to pool: {e}")

    def initialize_tables(self):
        if not self._is_available:
            logger.warning("DB unavailable, skipping table initialization.")
            return

        queries = get_create_tables_sql()
        with self.get_connection() as conn:
            if conn is None:
                return
            try:
                with conn.cursor() as cursor:
                    for query in queries:
                        cursor.execute(query)
                conn.commit()
                logger.info("Database tables initialized successfully.")
            except psycopg2.Error as e:
                conn.rollback()
                logger.error(f"Failed to initialize tables: {e}")

    def health_check(self) -> bool:
        if not self._is_available:
            return False
        with self.get_connection() as conn:
            if conn is None:
                return False
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                    return True
            except psycopg2.Error:
                return False

    def close_all(self):
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed.")

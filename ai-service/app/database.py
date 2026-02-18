"""
Database Interfaces and Implementations

Following Dependency Inversion Principle:
- High-level modules depend on abstractions (protocols)
- Low-level modules implement those abstractions
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Protocol
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings


class DatabaseConnection(Protocol):
    """
    Protocol (interface) for database connections.
    
    This allows us to swap implementations without changing dependent code.
    """
    
    def execute(self, query: str, params: tuple = None, fetch_results: bool = True) -> List[Dict]:
        """Execute a query and return results"""
        ...
    
    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute a query and return single result"""
        ...
    
    def commit(self) -> None:
        """Commit transaction"""
        ...
    
    def close(self) -> None:
        """Close connection"""
        ...


class PostgreSQLConnection:
    """
    PostgreSQL implementation of DatabaseConnection.
    
    Implements the connection protocol for PostgreSQL with pgvector support.
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize PostgreSQL connection.
        
        Args:
            connection_string: Optional custom connection string.
                             If not provided, uses settings.
        """
        self.connection_string = connection_string or settings.database_url
        self._conn = None
        self._cursor = None
    
    def _ensure_connection(self):
        """Lazy connection initialization"""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_db,
                cursor_factory=RealDictCursor
            )
            self._cursor = self._conn.cursor()
    
    def execute(self, query: str, params: tuple = None, fetch_results: bool = True) -> List[Dict]:
        """
        Execute query and return all results.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch_results: Whether to fetch results (default: True)
            
        Returns:
            List of result dictionaries (empty if fetch_results=False)
        """
        self._ensure_connection()
        self._cursor.execute(query, params)
        if fetch_results:
            return [dict(row) for row in self._cursor.fetchall()]
        return []
    
    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """
        Execute query and return single result.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Single result dictionary or None
        """
        self._ensure_connection()
        self._cursor.execute(query, params)
        result = self._cursor.fetchone()
        return dict(result) if result else None
    
    def commit(self) -> None:
        """Commit current transaction"""
        if self._conn:
            self._conn.commit()
    
    def close(self) -> None:
        """Close database connection"""
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()
        self._conn = None
        self._cursor = None
    
    def __enter__(self):
        """Context manager entry"""
        self._ensure_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            self.commit()
        self.close()


def get_db_connection() -> PostgreSQLConnection:
    """
    Factory function for database connections.
    
    Returns:
        PostgreSQL connection instance
    """
    return PostgreSQLConnection()


def init_vector_extension():
    """
    Initialize pgvector extension if not already enabled.
    
    This is idempotent and safe to call multiple times.
    """
    with get_db_connection() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✓ pgvector extension verified")


def test_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute_one("SELECT version();")
            print(f"✓ Connected to PostgreSQL: {result['version']}")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
    init_vector_extension()

"""
Database connection configuration
Handles PostgreSQL connection pooling
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'skill_barter'),
    'user': os.getenv('DB_USER', 'skill_barter_app'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Connection pool (reuses connections for performance)
connection_pool = None

def init_connection_pool():
    """
    Initialize database connection pool
    Call this once when app starts
    """
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **DB_CONFIG
        )
        print("✓ Database connection pool created")
    except Exception as e:
        print(f"✗ Failed to create connection pool: {e}")
        raise

def get_connection():
    """
    Get a connection from the pool
    Remember to return it when done!
    """
    if connection_pool:
        return connection_pool.getconn()
    else:
        raise Exception("Connection pool not initialized. Call init_connection_pool() first.")

def return_connection(conn):
    """
    Return connection to the pool
    """
    if connection_pool:
        connection_pool.putconn(conn)

def close_all_connections():
    """
    Close all connections in pool
    Call this when shutting down app
    """
    if connection_pool:
        connection_pool.closeall()
        print("✓ All database connections closed")

# Convenience function for one-off queries
def execute_query(query, params=None, fetch=True):
    """
    Execute a SQL query and return results
    
    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch: Whether to fetch results (False for INSERT/UPDATE/DELETE)
    
    Returns:
        List of dictionaries (if fetch=True) or None
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            return results
        else:
            conn.commit()
            return None
            
    except Exception as e:
        conn.rollback()
        print(f"✗ Query failed: {e}")
        raise
    finally:
        cursor.close()
        return_connection(conn)
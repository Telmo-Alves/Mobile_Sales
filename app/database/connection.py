"""
Database connection management for Mobile Sales
Handles Firebird database connections and SQL logging
"""

import fdb
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union
import re
from datetime import datetime

# Import config from parent app module
from ..config import FIREBIRD_CONFIG, WAREHOUSE_CONFIG

# Configure SQL logger
sql_logger = logging.getLogger('mobile_sales_sql')
sql_handler = logging.FileHandler('/var/log/apache2/mobile_sales_sql.log')
sql_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
sql_handler.setFormatter(sql_formatter)
sql_logger.addHandler(sql_handler)
sql_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

def get_session_context():
    """Get context information from Flask session if available"""
    try:
        from flask import session
        return {
            'user': session.get('user'),
            'vendedor': session.get('vendedor'),
            'nivel_acesso': session.get('nivel_acesso')
        }
    except:
        return None

def format_sql_with_params(sql: str, params: tuple = None) -> str:
    """Format SQL with parameters substituted for logging"""
    if not params:
        return sql
    
    formatted_sql = sql
    param_index = 0
    
    # Replace ? placeholders with actual parameter values
    def replace_param(match):
        nonlocal param_index
        if param_index < len(params):
            param_value = params[param_index]
            param_index += 1
            
            if param_value is None:
                return 'NULL'
            elif isinstance(param_value, str):
                # Escape single quotes and wrap in quotes
                escaped_value = param_value.replace("'", "''")
                return f"'{escaped_value}'"
            else:
                return str(param_value)
        return '?'
    
    # Use regex to replace ? placeholders
    formatted_sql = re.sub(r'\?', replace_param, formatted_sql)
    return formatted_sql

def log_sql_execution(sql: str, params: tuple = None, execution_time: float = None, error: str = None):
    """Log SQL execution with context information"""
    try:
        context = get_session_context()
        formatted_sql = format_sql_with_params(sql, params)
        
        context_info = ""
        if context:
            context_info = f" [User: {context.get('user', 'N/A')}, Vendedor: {context.get('vendedor', 'N/A')}, Nivel: {context.get('nivel_acesso', 'N/A')}]"
        
        if error:
            sql_logger.error(f"SQL ERROR{context_info}: {error}")
            sql_logger.error(f"SQL QUERY: {formatted_sql}")
        else:
            time_info = f" (Execution time: {execution_time:.3f}s)" if execution_time else ""
            sql_logger.info(f"SQL EXECUTED{context_info}{time_info}: {formatted_sql}")
            
    except Exception as e:
        logger.error(f"Failed to log SQL execution: {e}")

def get_db_connection():
    """Create and return a database connection - restored original working version"""
    try:
        return fdb.connect(**FIREBIRD_CONFIG)
    except Exception as e:
        error_msg = f"Erro na conexão à base de dados: {str(e)}"
        logger.error(error_msg)
        raise DatabaseError(error_msg)

@contextmanager
def database_transaction():
    """Context manager for database transactions with automatic rollback on error"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
        conn.commit()
        log_sql_execution("TRANSACTION COMMITTED", None)
    except Exception as e:
        if conn:
            conn.rollback()
            log_sql_execution("TRANSACTION ROLLED BACK", None, None, str(e))
        raise
    finally:
        if conn:
            conn.close()
            log_sql_execution("DATABASE CONNECTION CLOSED", None)
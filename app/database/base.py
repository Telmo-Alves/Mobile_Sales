"""
Base repository class with common database operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from .connection import get_db_connection, log_sql_execution, get_session_context, DatabaseError
from ..config import WAREHOUSE_CONFIG

class BaseRepository:
    """Base repository class with common database operations"""
    
    def __init__(self):
        self.warehouse_config = WAREHOUSE_CONFIG
    
    def get_warehouse_params(self) -> tuple:
        """Get warehouse parameters for queries"""
        return (
            self.warehouse_config.get('arm_ini', 1),
            self.warehouse_config.get('arm_fim', 999)
        )
    
    def execute_query(self, sql: str, params: tuple = None, fetchall: bool = True) -> Optional[List]:
        """Execute SELECT query and return results with proper logging"""
        conn = None
        cursor = None
        try:
            start_time = datetime.now()
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(sql, params or ())
            result = cursor.fetchall() if fetchall else cursor.fetchone()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            log_sql_execution(sql, params, execution_time)
            
            return result
            
        except Exception as e:
            log_sql_execution(sql, params, None, str(e))
            raise DatabaseError(f"Query execution failed: {str(e)}")
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def execute_command(self, sql: str, params: tuple = None) -> bool:
        """Execute INSERT/UPDATE/DELETE with commit and proper logging"""
        conn = None
        cursor = None
        try:
            start_time = datetime.now()
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(sql, params or ())
            conn.commit()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            log_sql_execution(sql, params, execution_time)
            
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            log_sql_execution(sql, params, None, str(e))
            raise DatabaseError(f"Command execution failed: {str(e)}")
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
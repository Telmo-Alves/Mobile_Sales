"""
User preferences repository for Mobile Sales application
Manages user-specific settings and filter preferences
"""

from typing import Dict, Optional, Any
from ..base import BaseRepository
import json

class UserPreferencesRepository(BaseRepository):
    """Repository for user preferences and settings"""
    
    def get_user_filters(self, vendedor_id: int, filter_type: str = 'existencias') -> Dict[str, Any]:
        """Get saved filters for a specific user and filter type"""
        try:
            sql = """
                SELECT FILTROS_JSON
                FROM User_Preferences 
                WHERE VENDEDOR = ? AND TIPO_FILTRO = ?
            """
            
            result = self.execute_query(sql, (vendedor_id, filter_type), fetchall=False)
            
            if result and result[0]:
                try:
                    return json.loads(result[0])
                except (json.JSONDecodeError, TypeError):
                    return {}
            
            return {}
            
        except Exception as e:
            print(f"Error getting user filters: {str(e)}")
            # If table doesn't exist or other error, return empty dict
            return {}
    
    def save_user_filters(self, vendedor_id: int, filters: Dict[str, Any], filter_type: str = 'existencias') -> bool:
        """Save user filters to database"""
        try:
            filters_json = json.dumps(filters)
            
            # Try to update existing record first
            sql_update = """
                UPDATE User_Preferences 
                SET FILTROS_JSON = ?, DATA_ATUALIZACAO = CURRENT_TIMESTAMP
                WHERE VENDEDOR = ? AND TIPO_FILTRO = ?
            """
            
            # Check if record exists first
            check_sql = """
                SELECT COUNT(*) FROM User_Preferences 
                WHERE VENDEDOR = ? AND TIPO_FILTRO = ?
            """
            
            count_result = self.execute_query(check_sql, (vendedor_id, filter_type), fetchall=False)
            record_exists = count_result and count_result[0] > 0
            
            if record_exists:
                # Update existing record
                self.execute_command(sql_update, (filters_json, vendedor_id, filter_type))
            else:
                # Insert new record
                sql_insert = """
                    INSERT INTO User_Preferences (VENDEDOR, TIPO_FILTRO, FILTROS_JSON)
                    VALUES (?, ?, ?)
                """
                self.execute_command(sql_insert, (vendedor_id, filter_type, filters_json))
            
            return True
            
        except Exception as e:
            print(f"Error saving user filters: {str(e)}")
            return False
    
    def clear_user_filters(self, vendedor_id: int, filter_type: str = 'existencias') -> bool:
        """Clear saved filters for a specific user and filter type"""
        try:
            sql = """
                DELETE FROM User_Preferences 
                WHERE VENDEDOR = ? AND TIPO_FILTRO = ?
            """
            
            self.execute_command(sql, (vendedor_id, filter_type))
            return True
            
        except Exception as e:
            print(f"Error clearing user filters: {str(e)}")
            return False
    
    def create_user_preferences_table(self):
        """Create the user preferences table if it doesn't exist"""
        try:
            sql = """
                CREATE TABLE User_Preferences (
                    id INTEGER NOT NULL,
                    vendedor INTEGER NOT NULL,
                    tipo_filtro VARCHAR(50) NOT NULL,
                    filtros_json BLOB SUB_TYPE TEXT,
                    data_criacao TIMESTAMP,
                    data_atualizacao TIMESTAMP,
                    PRIMARY KEY (id)
                )
            """
            
            self.execute_command(sql, ())
            
            # Create unique index
            sql_index = """
                CREATE UNIQUE INDEX UQ_User_Preferences_Vendedor_Tipo 
                ON User_Preferences (vendedor, tipo_filtro)
            """
            
            self.execute_command(sql_index, ())
            
        except Exception as e:
            # Table might already exist, that's ok
            pass
    
    def get_all_user_preferences(self, vendedor_id: int) -> Dict[str, Dict[str, Any]]:
        """Get all preferences for a user"""
        try:
            sql = """
                SELECT tipo_filtro, filtros_json
                FROM User_Preferences 
                WHERE vendedor = ?
            """
            
            results = self.execute_query(sql, (vendedor_id,))
            
            preferences = {}
            for row in results:
                tipo_filtro = row[0]
                try:
                    filtros = json.loads(row[1]) if row[1] else {}
                    preferences[tipo_filtro] = filtros
                except (json.JSONDecodeError, TypeError):
                    preferences[tipo_filtro] = {}
            
            return preferences
            
        except Exception as e:
            return {}
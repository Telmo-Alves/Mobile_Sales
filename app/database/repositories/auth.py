"""
Authentication repository for user login operations
"""

from typing import Optional, Dict
from ..base import BaseRepository

class AuthRepository(BaseRepository):
    """Repository for authentication operations"""
    
    def authenticate_user(self, utilizador: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        sql = """
            SELECT Utilizador, Senha, Vendedor, Nivel
            FROM Utiliza_Web
            WHERE Utilizador = ? AND Senha = ?
        """
        
        result = self.execute_query(sql, (utilizador, password), fetchall=False)
        
        if result:
            return {
                'utilizador': result[0],
                'vendedor': result[2],
                'nivel_acesso': result[3] or 0
            }
        
        return None
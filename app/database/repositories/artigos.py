"""
Repository for articles/products operations
"""

from typing import Optional, Dict
from ..base import BaseRepository


class ArtigosRepository(BaseRepository):
    """Repository for articles/products operations"""
    
    def get_product_info(self, codigo: str) -> Optional[Dict]:
        """Get product basic information"""
        sql = """
            SELECT Descricao, P_Qt1, P_Qt2 
            FROM Artigos 
            WHERE Codigo = ?
        """
        
        result = self.execute_query(sql, (codigo,), fetchall=False)
        
        if result:
            return {
                'descricao': result[0],
                'p_qt1': result[1] or 0,
                'p_qt2': result[2] or 0
            }
        
        return None
    
    def get_product_prices(self, codigo: str, lote: str) -> Optional[Dict]:
        """Get specific prices for product/lot"""
        sql = """
            SELECT Preco1, Preco2 
            FROM RelArtLote_Preco 
            WHERE Codigo = ? AND Lote = ?
        """
        
        result = self.execute_query(sql, (codigo, lote), fetchall=False)
        
        if result:
            return {
                'preco1': result[0] or 0,
                'preco2': result[1] or 0
            }
        
        return None
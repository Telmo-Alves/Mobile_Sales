"""
Repository for clients operations
"""

from typing import Optional, List, Dict
from ..base import BaseRepository


class ClientesRepository(BaseRepository):
    """Repository for clients operations"""
    
    def get_clients_for_vendor(self, vendedor: int) -> List:
        """Get clients list for vendor"""
        sql = """
            SELECT l.cliente, l.Nome1, c.Situacao, rc2.vendedor 
            FROM Locais_Entrega l
            LEFT OUTER JOIN clientes c ON c.cliente = l.cliente
            LEFT OUTER JOIN Rel_Cli_Vend2 rc2 ON rc2.cliente = l.cliente
            WHERE ( c.situacao IN ( 'ACT', 'MANUT' ) ) 
                AND ( ( l.vendedor = ? ) OR ( rc2.vendedor = ? ) OR ( ? = 1 ) )
            ORDER BY l.Nome1
        """
        
        return self.execute_query(sql, (vendedor, vendedor, vendedor))
    
    def get_client_info(self, cliente: str, local: str = 'SEDE') -> Optional[Dict]:
        """Get client information"""
        sql = """
            SELECT Nome1 
            FROM Locais_Entrega 
            WHERE Cliente = ? AND local_id = ?
        """
        
        result = self.execute_query(sql, (cliente, local), fetchall=False)
        return {'nome': result[0]} if result else None
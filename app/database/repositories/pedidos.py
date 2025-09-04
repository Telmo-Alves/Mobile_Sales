"""
Repository for orders operations
"""

from typing import Optional, List, Dict, Any
from ..base import BaseRepository
from ...config import FIREBIRD_CONFIG


class PedidosRepository(BaseRepository):
    """Repository for orders operations"""
    
    def get_orders_list(self, vendedor: int) -> List:
        """Get orders list for vendor"""
        sql = """
            SELECT FIRST 100
                P.Pedido, P.Quantidade, P.Preco, P.Lote, A.Descricao, 
                C.Nome1 as Cliente, P.Estado, P.Dt_Registo
            FROM Pda_Pedidos P 
            LEFT OUTER JOIN Artigos A ON A.Codigo = P.Codigo 
            LEFT OUTER JOIN Locais_Entrega C ON C.Cliente = P.Cliente AND C.local_id = 'SEDE'
            WHERE ( ( P.Vendedor = ? ) OR ( ? = 1 ) OR ( ? = 99 ) )
            ORDER BY P.Dt_Registo DESC, P.Pedido DESC
        """
        
        return self.execute_query(sql, (vendedor, vendedor, vendedor))
    
    def cancel_order(self, pedido_num: int, vendedor: int) -> Dict[str, Any]:
        """Cancel an order"""
        # Check if order exists and permissions
        check_sql = """
            SELECT Estado, Vendedor 
            FROM Pda_Pedidos 
            WHERE Pedido = ?
        """
        
        order_data = self.execute_query(check_sql, (pedido_num,), fetchall=False)
        
        if not order_data:
            return {'success': False, 'error': 'Pedido não encontrado'}
        
        estado_atual, vendedor_pedido = order_data
        
        # Check permissions
        if not ((vendedor_pedido == vendedor) or (vendedor in [1, 99])):
            return {'success': False, 'error': 'Sem permissões para anular este pedido'}
        
        # Check if already cancelled/finished
        if estado_atual in ['C', 'F']:
            estado_desc = 'Cancelado' if estado_atual == 'C' else 'Finalizado'
            return {'success': False, 'error': f'Pedido já está {estado_desc}'}
        
        # Cancel order
        cancel_sql = """
            UPDATE Pda_Pedidos 
            SET Estado = 'C'
            WHERE Pedido = ?
        """
        
        success = self.execute_command(cancel_sql, (pedido_num,))
        
        if success:
            return {'success': True, 'message': f'Pedido {pedido_num} anulado com sucesso'}
        else:
            return {'success': False, 'error': 'Erro ao anular pedido'}
    
    def create_order(self, order_data: Dict[str, Any]) -> bool:
        """Create new order"""
        utilizador = FIREBIRD_CONFIG['user']
        armazem_fixo = self.warehouse_config.get('arm_ini', 1)
        marca = ''  # Default empty
        
        sql = """
            INSERT INTO PDA_PEDIDOS (
                PEDIDO, UTILIZADOR, DT_REGISTO, DT_ENTREGA, CODIGO, ARMAZEM, LOTE,
                QUANTIDADE, MARCA, CLIENTE, LOCAL_ID, PRECO, ESTADO, VENDEDOR,
                OBSERVACOES, OBSERVACOES2, AVISOS
            ) VALUES (
                0, ?, CURRENT_TIMESTAMP, ?,
                ?, ?, ?, ?, ?, ?, ?, ?,
                'P', ?, ?, ?, ?
            )
        """
        
        params = (
            utilizador,
            order_data.get('entrega', ''),
            order_data.get('codigo', ''),
            armazem_fixo,
            order_data.get('lote', ''),
            order_data.get('quantidade', 0),
            marca,
            order_data.get('cliente', ''),
            order_data.get('local_entrega', ''),
            order_data.get('preco', 0),
            order_data.get('vendedor', 0),
            order_data.get('obs', ''),
            order_data.get('obs2', ''),
            order_data.get('avisos', '0000000')
        )
        
        return self.execute_command(sql, params)
"""
Repository for clients operations - Enhanced for Mapa de Bordo (Customer Dashboard)
Based on legacy PHP mapabordocli functionality
"""

from typing import Optional, List, Dict
from ..base import BaseRepository


class ClientesRepository(BaseRepository):
    """Repository for clients operations"""
    
    def get_clients_for_vendor(self, vendedor: int) -> List:
        """Get clients list for vendor - Enhanced for Mapa de Bordo"""
        # Determine access level based on vendedor
        nivel = 0
        if vendedor in [1, 2]:
            nivel = 1
        elif vendedor in [20, 88, 99]:
            nivel = 99
            
        sql = """
            SELECT l.cliente, l.Nome1, c.Situacao, rc2.vendedor 
            FROM Locais_Entrega l
            LEFT OUTER JOIN clientes c ON c.cliente = l.cliente
            LEFT OUTER JOIN Rel_Cli_Vend2 rc2 ON rc2.cliente = l.cliente
            WHERE ( c.situacao IN ( 'ACT', 'MANUT' ) ) 
                AND ( ( l.vendedor = ? ) OR ( rc2.vendedor = ? ) OR ( ? > 0 ) )
            ORDER BY l.Nome1
        """
        
        return self.execute_query(sql, (vendedor, vendedor, nivel))
    
    def get_client_info(self, cliente: str, local: str = 'SEDE') -> Optional[Dict]:
        """Get client information"""
        sql = """
            SELECT Nome1 
            FROM Locais_Entrega 
            WHERE Cliente = ? AND local_id = ?
        """
        
        result = self.execute_query(sql, (cliente, local), fetchall=False)
        return {'nome': result[0]} if result else None
    
    def get_customer_dashboard_data(self, cliente_id: str, vendedor_id: int, data_ref: str = "NOW") -> Optional[Dict]:
        """Get comprehensive customer dashboard data (Mapa de Bordo)"""
        # Determine access level
        nivel = 0
        if vendedor_id in [1, 2]:
            nivel = 1
        elif vendedor_id in [20, 88, 99]:
            nivel = 99
        
        try:
            # Execute the stored procedure/function to get dashboard data
            sql = """
            SELECT R_Cliente, R_Nome, R_Data, R_Plafond, R_Plafond_Ext,
                   R_Plafond_Resp, R_Obj_Vendas, R_Perc_Obj, R_Credito_Cort,
                   R_Data_Cort, R_Val_Letras, R_Val_CC, R_Val_Factoring, R_Val_PreData,
                   R_Val_Encom, R_Vendas_Actual, R_Vendas_Ant, R_Vendedor, R_Plafond_OCDE,
                   rc2.Vendedor
            FROM Busca_MapaBordo_Cli(?, ?) B
            LEFT OUTER JOIN Rel_Cli_Vend2 rc2 ON rc2.cliente = b.R_cliente
            WHERE (R_Vendedor = ?) OR (RC2.Vendedor = ?) OR ? > 0
            """
            
            result = self.execute_query(sql, (cliente_id, data_ref, vendedor_id, vendedor_id, nivel), fetchall=False)
            
            if not result:
                return None
                
            # Map the result to a dictionary for easier handling
            dashboard_data = {
                'cliente': result[0],
                'nome': result[1],
                'data': result[2],
                'plafond': result[3] or 0,
                'plafond_ext': result[4] or 0,
                'plafond_resp': result[5] or 0,
                'obj_vendas': result[6] or 0,
                'perc_obj': result[7] or 0,
                'credito_cort': result[8] or 0,
                'data_cort': result[9],
                'val_letras': result[10] or 0,
                'val_cc': result[11] or 0,
                'val_factoring': result[12] or 0,
                'val_predata': result[13] or 0,
                'val_encom': result[14] or 0,
                'vendas_actual': result[15] or 0,
                'vendas_ant': result[16] or 0,
                'vendedor': result[17],
                'plafond_ocde': result[18] or 0
            }
            
            # Calculate totals
            dashboard_data['val_total'] = (dashboard_data['val_letras'] + 
                                         dashboard_data['val_cc'] + 
                                         dashboard_data['val_factoring'] + 
                                         dashboard_data['val_encom'] + 
                                         dashboard_data['val_predata'])
            
            dashboard_data['plafond_total'] = dashboard_data['plafond']
            dashboard_data['plafond_seg_total'] = dashboard_data['plafond_ext'] + dashboard_data['plafond_ocde']
            
            # Calculate status (over limit or not)
            dashboard_data['over_limit'] = dashboard_data['val_total'] > dashboard_data['plafond_total']
            
            return dashboard_data
            
        except Exception as e:
            return None

    def format_currency(self, value) -> str:
        """Format currency values like the PHP original"""
        if value is None:
            return "0,00"
        return "{:,.2f}".format(float(value)).replace(",", " ").replace(".", ",")
"""
Repository for client reservations operations
"""

from typing import List
from ..base import BaseRepository


class ReservasRepository(BaseRepository):
    """Repository for client reservations operations"""
    
    def get_reservations(self, codigo: str, lote: str, fornecedor: str = '', vendedor: int = 0) -> List:
        """Get client reservations for product/lot"""
        arm_ini, arm_fim = self.get_warehouse_params()
        
        try:
            fornecedor_int = int(fornecedor) if fornecedor and fornecedor.strip() else 0
        except (ValueError, AttributeError):
            fornecedor_int = 0
        
        sql = """
            SELECT I.RData, I.RQuant1, I.RQuant2, I.RPreco_Un, I.RNomeTerc, 
                   I.RDataEnt, I.RCodigo, I.RLote, I.RSerie, I.RNumero, 
                   I.RTerceiro, L.Vendedor, I.RLinha, I.RArmazem, A.Descricao
            FROM Inq_Exist_Lote_Enc2(?, ?, ?, ?, ?, '31.12.3000', 'E', 'S', 1, 2, 2) I
            LEFT OUTER JOIN Locais_Entrega L ON L.Cliente = I.RTerceiro AND L.Local_ID = 'SEDE'
            LEFT OUTER JOIN Artigos A ON A.Codigo = I.RCodigo
        """
        
        reservas_raw = self.execute_query(sql, (codigo, lote, arm_ini, arm_fim, fornecedor_int))
        
        # Apply filters like PHP original
        reservas_filtradas = []
        for reserva in reservas_raw:
            vendedor_reserva = reserva[11] if reserva[11] is not None else 0
            quant_pedida = float(reserva[1]) if reserva[1] is not None else 0.0
            quant_entregue = float(reserva[2]) if reserva[2] is not None else 0.0
            quant_falta = quant_pedida - quant_entregue
            
            # Filter: authorized vendor AND quantity pending > 0.1
            if ((vendedor_reserva == vendedor) or (vendedor in [1, 2, 99])) and (quant_falta > 0.1):
                reservas_filtradas.append(reserva)
        
        return reservas_filtradas
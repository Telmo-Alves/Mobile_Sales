"""
Repository for requisitions operations
"""

from typing import List
from ..base import BaseRepository


class RequisicoesRepository(BaseRepository):
    """Repository for requisitions operations"""
    
    def get_requisitions(self, codigo: str, lote: str, fornecedor: str = '') -> List:
        """Get requisitions for product/lot based on the original PHP code"""
        try:
            fornecedor_int = int(fornecedor) if fornecedor and fornecedor.strip() else 0
        except (ValueError, AttributeError):
            fornecedor_int = 0
        
        # Based on the PHP code: Inq_Exist_Lote_Enc2(codigo, lote, 3, 4, fornecedor, '31.12.3000', 'O', 'S', 1, 2, 2)
        sql = """
            SELECT RDataEnt, RSituacao, RNomeTerc, (RQuant1 - RQuant2) as RQtEnc, 
                   RCodigo, RLote, RTerceiro
            FROM Inq_Exist_Lote_Enc2(?, ?, 3, 4, ?, '31.12.3000', 'O', 'S', 1, 2, 2) 
            ORDER BY ROrdemSitua, RDataEnt
        """
        
        requisitions_raw = self.execute_query(sql, (codigo, lote, fornecedor_int))
        
        # Filter out entries with quantity <= 0 (similar to original PHP logic)
        requisitions_filtered = []
        for req in requisitions_raw:
            quant = float(req[3]) if req[3] is not None else 0.0
            if quant > 0:
                requisitions_filtered.append(req)
        
        return requisitions_filtered
    
    def get_supplier_name(self, fornecedor: str) -> str:
        """Get supplier name by ID"""
        try:
            fornecedor_int = int(fornecedor) if fornecedor and fornecedor.strip() else 0
        except (ValueError, AttributeError):
            return ""
            
        if fornecedor_int == 0:
            return ""
            
        sql = "SELECT Nome1 FROM Fornecedores WHERE Fornecedor = ?"
        result = self.execute_query(sql, (fornecedor_int,))
        
        if result and len(result) > 0:
            return result[0][0] if result[0][0] else ""
        
        return ""
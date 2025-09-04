"""
Repository for stock/existencias operations
"""

from typing import Optional, List, Dict, Any
from ..base import BaseRepository


class ExistenciasRepository(BaseRepository):
    """Repository for stock/existencias operations"""
    
    def search_products(self, codigo_artigo: str, enc_forn: str = 'S') -> List:
        """Search products using Inq_Exist_Lote_Pda procedure"""
        arm_ini, arm_fim = self.get_warehouse_params()
        
        sql = """
            SELECT RDescricao, RCodigo, RCodigoSubstituto, 
                   SUM(RExist) as TotalExist,
                   SUM(REncCli) as TotalEncCli,
                   SUM(RExist - REncCli) as Disponivel
            FROM Inq_Exist_Lote_Pda(?, ?, ?, ?, 'TUDO', 0, '31.12.3000', ?, '31.12.3000', 0, 'S', 1, 2, 2)
            WHERE RCodigo STARTING WITH ?
            GROUP BY RDescricao, RCodigo, RCodigoSubstituto
            ORDER BY RCodigo ASC
        """
        
        codigo_fim = codigo_artigo + 'z'
        params = (codigo_artigo, codigo_fim, arm_ini, arm_fim, enc_forn, codigo_artigo)
        
        return self.execute_query(sql, params)
    
    def get_product_details(self, codigo: str, enc_forn: str = 'S') -> List:
        """Get detailed product information by lot"""
        arm_ini, arm_fim = self.get_warehouse_params()
        
        sql = """
            SELECT RCodigo, RLote, RLoteFor, RExist, (RExist - REncCli + REncFor) as RStkDisp,
                   REncCli, RFornec, RNomeFor, RDescricao, RTipoSitua, RPvp1, RPvp2, RPreco_UN, RMoeda,
                   RCond_Entrega, RChave, RTipoNivel, RNivel, RPvp3, RPvp4, RTipoSituaDesc, RCodigo_Cor,
                   RArmazem, RPreco_Compra, RSigla, RFixacao, RForma_Pag_Desc, RPrazo_NDias
            FROM Inq_Exist_Lote_Pda_2(?, ?, ?, ?, 'ACT', 0, '31.12.3000', ?, '31.12.3000', 0, 'S', 1, 2, 2)
            ORDER BY RChave ASC, RExist ASC, ROrdem
        """
        
        params = (codigo, codigo, arm_ini, arm_fim, enc_forn)
        return self.execute_query(sql, params)
    
    def get_lab_results(self, codigo: str, lote: str) -> Optional[Dict]:
        """Get laboratory results for product lot"""
        sql = """
            SELECT FIRST 1 L.Ne_Valor, L.Ne_Cv, L.Uster_CVM, L.Uster_PNTFinos2, L.Uster_PNTGrossos2, L.Uster_Neps_2,
                   L.Rkm_Valor, L.Rkm_Cv, L.Rkm_Along_Valor, L.Rkm_Along_Cv, L.Tipo_Torcao, L.Torcao_TPI_Valor, L.Tipo_Torcao_S,
                   L.Torcao_TPI_Valor_S, T.Nr_Fios, L.Uster_Pilosidade, L.Uster_Pilosidade_Cv, L.Uster_Neps_3, L.Tipo_Processo
            FROM Ficha_Lab_Lote L 
            LEFT OUTER JOIN Tipo_Torcedura T ON T.Tipo = L.Tipo_Torcedura 
            WHERE L.Codigo = ? AND L.Lote = ? 
            ORDER BY L.nr_relatorio DESC
        """
        
        result = self.execute_query(sql, (codigo, lote), fetchall=False)
        
        if result:
            # Format results as in PHP
            tipo_processo = result[18] if len(result) > 18 else None
            pf_index = 3 if tipo_processo == "O" else 3
            pg_index = 4 if tipo_processo == "O" else 4
            np_index = 17 if tipo_processo == "O" else 5
            
            return {
                'pf': result[pf_index],
                'pg': result[pg_index], 
                'np': result[np_index],
                'rk': result[6]  # Rkm_Valor
            }
        
        return None
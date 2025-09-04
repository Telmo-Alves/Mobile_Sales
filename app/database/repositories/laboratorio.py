"""
Laboratory repository for Mobile Sales application
"""

from typing import Dict, List, Optional
from ..base import BaseRepository

class LaboratorioRepository(BaseRepository):
    """Repository for laboratory results and observations"""
    
    def get_lab_results(self, codigo: str, lote: str) -> Optional[Dict]:
        """Get complete laboratory results matching RISATEL PDF format"""
        
        # Use T.Nr_Fios, L.* query as requested
        sql = """
            SELECT FIRST 1 T.Nr_Fios, L.*
            FROM Ficha_Lab_Lote L
            LEFT OUTER JOIN Tipo_Torcedura T ON T.Tipo = L.Tipo_Torcedura
            WHERE L.Codigo = ? AND L.Lote = ?
            ORDER BY L.nr_relatorio DESC
        """
        
        results = self.execute_query(sql, (codigo, lote))
        
        if results and len(results) > 0:
            row = results[0]
            
            # Map results based on T.Nr_Fios, L.* query
            # Based on the exact field order you provided:
            lab_data = {
                # T.Nr_Fios is first (position 0)
                'nr_fios': row[0],                           # NR_FIOS
                
                # L.* columns follow (positions 1+):
                'nr_relatorio': row[1] if len(row) > 1 else None,        # NR_RELATORIO
                'data_registo': row[2] if len(row) > 2 else None,        # DT_REGISTO  
                'nr_teste_fisico': row[3] if len(row) > 3 else None,     # NR_TESTE_FISICO
                'data_teste_fisico': row[4] if len(row) > 4 else None,   # DATA_TESTE_FISICO
                'data_teste_quimico': row[5] if len(row) > 5 else None,  # DATA_TESTE_QUIMICO
                'codigo': row[6] if len(row) > 6 else codigo,            # CODIGO
                'lote': row[7] if len(row) > 7 else lote,                # LOTE
                'tipo_processo': row[8] if len(row) > 8 else None,       # TIPO_PROCESSO
                'composicao': row[9] if len(row) > 9 else None,          # COMPOSICAO
                'tipo_torcedura': row[10] if len(row) > 10 else None,    # TIPO_TORCEDURA
                'tipo_uso_fio': row[11] if len(row) > 11 else None,      # TIPO_USO_FIO
                'tipo_acond': row[12] if len(row) > 12 else None,        # TIPO_ACOND
                'operador_fisico': row[13] if len(row) > 13 else None,   # OPERADOR_FISICO
                'operador_quimico': row[14] if len(row) > 14 else None,  # OPERADOR_QUIMICO
                'fornecedor': row[15] if len(row) > 15 else None,        # FORNECEDOR
                'hr': row[16] if len(row) > 16 else None,                # HR (Humidade Relativa)
                'ne_teorico': row[17] if len(row) > 17 else None,        # NE_TEORICO
                'ne_valor': row[18] if len(row) > 18 else None,          # NE_VALOR
                'ne_cv': row[19] if len(row) > 19 else None,             # NE_CV
                'uster_u': row[20] if len(row) > 20 else None,           # USTER_U
                'uster_cv': row[21] if len(row) > 21 else None,          # USTER_CV
                'uster_cvm': row[22] if len(row) > 22 else None,         # USTER_CVM
                'uster_pnt_finos_40': row[23] if len(row) > 23 else None, # USTER_PNTFINOS (-40%)
                'uster_pnt_finos': row[24] if len(row) > 24 else None,   # USTER_PNTFINOS2 (-50%)
                'uster_pnt_grossos_35': row[25] if len(row) > 25 else None, # USTER_PNTGROSSOS (+35%)
                'uster_pnt_grossos': row[26] if len(row) > 26 else None, # USTER_PNTGROSSOS2 (+50%)
                'uster_neps': row[27] if len(row) > 27 else None,        # USTER_NEPS
                'uster_neps_1': row[28] if len(row) > 28 else None,      # USTER_NEPS_1 (+140%)
                'uster_neps_2': row[29] if len(row) > 29 else None,      # USTER_NEPS_2 (+200%)
                'uster_neps_3': row[30] if len(row) > 30 else None,      # USTER_NEPS_3 (+280%)
                'uster_rel_cnt': row[31] if len(row) > 31 else None,     # USTER_REL_CNT
                'uster_rel_cnt_min': row[32] if len(row) > 32 else None, # USTER_REL_CNT_MIN
                'uster_rel_cnt_max': row[33] if len(row) > 33 else None, # USTER_REL_CNT_MAX
                'rkm_valor_tenac': row[34] if len(row) > 34 else None,   # RKM_VALOR_TENAC
                'rkm_cv_tenac': row[35] if len(row) > 35 else None,      # RKM_CV_TENAC
                'rkm_valor': row[36] if len(row) > 36 else None,         # RKM_VALOR
                'rkm_cv': row[37] if len(row) > 37 else None,            # RKM_CV
                'rkm_along_valor': row[38] if len(row) > 38 else None,   # RKM_ALONG_VALOR
                'rkm_along_cv': row[39] if len(row) > 39 else None,      # RKM_ALONG_CV
                'rkm_energia_valor': row[40] if len(row) > 40 else None, # RKM_ENERGIA_VALOR
                'rkm_energia_cv': row[41] if len(row) > 41 else None,    # RKM_ENERGIA_CV
                'tipo_torcao': row[42] if len(row) > 42 else None,       # TIPO_TORCAO
                'torcao_tpi_valor': row[43] if len(row) > 43 else None,  # TORCAO_TPI_VALOR
                'torcao_tpi_cv': row[44] if len(row) > 44 else None,     # TORCAO_TPI_CV
                'torcao_tpm_valor': row[45] if len(row) > 45 else None,  # TORCAO_TPM_VALOR
                'torcao_tpm_cv': row[46] if len(row) > 46 else None,     # TORCAO_TPM_CV
                'torcao_tpi_alfa': row[47] if len(row) > 47 else None,   # TORCAO_TPI_ALFA
                'tipo_torcao_s': row[48] if len(row) > 48 else None,     # TIPO_TORCAO_S
                'torcao_tpi_valor_s': row[49] if len(row) > 49 else None, # TORCAO_TPI_VALOR_S
                'torcao_tpi_cv_s': row[50] if len(row) > 50 else None,   # TORCAO_TPI_CV_S
                'uster_pilosidade': row[65] if len(row) > 65 else None,  # USTER_PILOSIDADE
                'uster_pilosidade_cv': row[66] if len(row) > 66 else None, # USTER_PILOSIDADE_CV
            }
            
            return lab_data
        
        return None
    
    def get_process_type_for_user(self, vendedor: int) -> str:
        """Get process type for user (TProcesso from session)"""
        # This would need to be implemented based on your user/session logic
        # For now, return 'O' as default (can be customized based on user)
        return 'O'
    
    def format_lab_value(self, value, decimal_places: int = 2) -> str:
        """Format laboratory values for display"""
        if value is None:
            return "-"
        
        try:
            float_val = float(value)
            if decimal_places == 0:
                return f"{float_val:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            else:
                return f"{float_val:,.{decimal_places}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return str(value) if value else "-"
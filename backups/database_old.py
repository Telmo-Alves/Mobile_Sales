"""
Database abstraction layer for Mobile Sales
Centralizes database connections and common operations
"""

import fdb
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union
from config import FIREBIRD_CONFIG, WAREHOUSE_CONFIG
import re
from datetime import datetime

# Configure SQL logger
sql_logger = logging.getLogger('mobile_sales_sql')
sql_handler = logging.FileHandler('/var/log/apache2/mobile_sales_sql.log')
sql_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
sql_handler.setFormatter(sql_formatter)
sql_logger.addHandler(sql_handler)
sql_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

def get_session_context():
    """Get context information from Flask session if available"""
    try:
        from flask import session
        return {
            'user': session.get('user'),
            'vendedor': session.get('vendedor'),
            'nivel_acesso': session.get('nivel_acesso')
        }
    except:
        return None

def format_sql_with_params(sql: str, params: tuple = None) -> str:
    """Format SQL with parameters substituted for logging"""
    if not params:
        return sql
    
    formatted_sql = sql
    param_index = 0
    
    # Replace ? placeholders with actual parameter values
    def replace_param(match):
        nonlocal param_index
        if param_index < len(params):
            param_value = params[param_index]
            param_index += 1
            
            # Format parameter value for SQL
            if param_value is None:
                return 'NULL'
            elif isinstance(param_value, str):
                return f"'{param_value.replace(chr(39), chr(39)+chr(39))}'"  # Escape single quotes
            elif isinstance(param_value, (int, float)):
                return str(param_value)
            elif isinstance(param_value, datetime):
                return f"'{param_value.strftime('%Y-%m-%d %H:%M:%S')}'"
            else:
                return f"'{str(param_value)}'"
        return '?'
    
    # Replace all ? with parameter values
    formatted_sql = re.sub(r'\?', replace_param, formatted_sql)
    return formatted_sql

def log_sql_execution(operation: str, sql: str, params: tuple = None, result_count: int = None, error: str = None, context: dict = None):
    """Log SQL execution details"""
    try:
        formatted_sql = format_sql_with_params(sql, params)
        
        # Build log message
        log_message = f"[{operation}] {formatted_sql}"
        
        if result_count is not None:
            log_message += f" --> {result_count} rows"
        
        # Add context information if available
        if context:
            context_parts = []
            if context.get('user'):
                context_parts.append(f"User: {context['user']}")
            if context.get('vendedor'):
                context_parts.append(f"Vendedor: {context['vendedor']}")
            if context.get('nivel_acesso'):
                context_parts.append(f"Nivel: {context['nivel_acesso']}")
            if context_parts:
                log_message += f" | {', '.join(context_parts)}"
        
        if error:
            log_message += f" --> ERROR: {error}"
            sql_logger.error(log_message)
        else:
            sql_logger.info(log_message)
            
    except Exception as e:
        sql_logger.error(f"Error logging SQL: {str(e)}")

class DatabaseManager:
    """Centralized database connection and query management"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or FIREBIRD_CONFIG
        self._connection = None
    
    def get_connection(self):
        """Get database connection with error handling"""
        try:
            if self._connection and not self._connection.closed:
                return self._connection
            
            self._connection = fdb.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                charset=self.config['charset']
            )
            return self._connection
            
        except Exception as e:
            logger.error(f"Erro de conexão à base de dados: {str(e)}")
            raise
    
    def close_connection(self):
        """Close database connection safely"""
        if self._connection and not self._connection.closed:
            try:
                self._connection.close()
            except Exception as e:
                logger.error(f"Erro ao fechar conexão: {str(e)}")
            finally:
                self._connection = None
    
    @contextmanager
    def get_cursor(self, auto_commit: bool = False):
        """Context manager for database cursors with automatic cleanup"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            yield cursor
            
            if auto_commit:
                conn.commit()
                
        except Exception as e:
            if conn and auto_commit:
                conn.rollback()
            logger.error(f"Erro na operação de base de dados: {str(e)}")
            raise
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def execute_query(self, sql: str, params: tuple = None, fetchall: bool = True, context: dict = None) -> Optional[List]:
        """Execute SELECT query and return results"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, params or ())
                result = cursor.fetchall() if fetchall else cursor.fetchone()
                
                # Log successful query
                result_count = len(result) if fetchall and result else (1 if result else 0)
                session_context = context or get_session_context()
                log_sql_execution("SELECT", sql, params, result_count, context=session_context)
                
                return result
        except Exception as e:
            # Log failed query
            session_context = context or get_session_context()
            log_sql_execution("SELECT", sql, params, error=str(e), context=session_context)
            raise
    
    def execute_insert(self, sql: str, params: tuple = None, context: dict = None) -> bool:
        """Execute INSERT/UPDATE/DELETE with commit"""
        try:
            with self.get_cursor(auto_commit=True) as cursor:
                cursor.execute(sql, params or ())
                
                # Log successful insert/update/delete
                operation = sql.strip().split()[0].upper()
                session_context = context or get_session_context()
                log_sql_execution(operation, sql, params, result_count=1, context=session_context)
                
                return True
        except Exception as e:
            # Log failed insert/update/delete
            operation = sql.strip().split()[0].upper() 
            session_context = context or get_session_context()
            log_sql_execution(operation, sql, params, error=str(e), context=session_context)
            logger.error(f"Erro na inserção: {str(e)}")
            return False
    
    def execute_procedure(self, procedure_name: str, params: tuple = None) -> List:
        """Execute stored procedure and return results"""
        sql = f"SELECT * FROM {procedure_name}({','.join(['?' for _ in params or []])})"
        
        # The logging will be handled by execute_query
        return self.execute_query(sql, params)

# Global database instance
db = DatabaseManager()

class BaseRepository:
    """Base repository class with common database operations"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or db
        self.warehouse_config = WAREHOUSE_CONFIG
    
    def get_warehouse_params(self) -> tuple:
        """Get warehouse parameters for queries"""
        return (
            self.warehouse_config.get('arm_ini', 1),
            self.warehouse_config.get('arm_fim', 999)
        )

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
        
        return self.db.execute_query(sql, params)
    
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
        return self.db.execute_query(sql, params)
    
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
        
        result = self.db.execute_query(sql, (codigo, lote), fetchall=False)
        
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
        
        return self.db.execute_query(sql, (vendedor, vendedor, vendedor))
    
    def cancel_order(self, pedido_num: int, vendedor: int) -> Dict[str, Any]:
        """Cancel an order"""
        # Check if order exists and permissions
        check_sql = """
            SELECT Estado, Vendedor 
            FROM Pda_Pedidos 
            WHERE Pedido = ?
        """
        
        order_data = self.db.execute_query(check_sql, (pedido_num,), fetchall=False)
        
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
        
        success = self.db.execute_insert(cancel_sql, (pedido_num,))
        
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
        
        return self.db.execute_insert(sql, params)

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
        
        reservas_raw = self.db.execute_query(sql, (codigo, lote, arm_ini, arm_fim, fornecedor_int))
        
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
        
        return self.db.execute_query(sql, (vendedor, vendedor, vendedor))
    
    def get_client_info(self, cliente: str, local: str = 'SEDE') -> Optional[Dict]:
        """Get client information"""
        sql = """
            SELECT Nome1 
            FROM Locais_Entrega 
            WHERE Cliente = ? AND local_id = ?
        """
        
        result = self.db.execute_query(sql, (cliente, local), fetchall=False)
        return {'nome': result[0]} if result else None

class ArtigosRepository(BaseRepository):
    """Repository for articles/products operations"""
    
    def get_product_info(self, codigo: str) -> Optional[Dict]:
        """Get product basic information"""
        sql = """
            SELECT Descricao, P_Qt1, P_Qt2 
            FROM Artigos 
            WHERE Codigo = ?
        """
        
        result = self.db.execute_query(sql, (codigo,), fetchall=False)
        
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
        
        result = self.db.execute_query(sql, (codigo, lote), fetchall=False)
        
        if result:
            return {
                'preco1': result[0] or 0,
                'preco2': result[1] or 0
            }
        
        return None

class AuthRepository(BaseRepository):
    """Repository for authentication operations"""
    
    def authenticate_user(self, utilizador: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        sql = """
            SELECT Utilizador, Senha, Vendedor, Nivel
            FROM Utiliza_Web
            WHERE Utilizador = ? AND Senha = ?
        """
        
        result = self.db.execute_query(sql, (utilizador, password), fetchall=False)
        
        if result:
            return {
                'utilizador': result[0],
                'vendedor': result[2],
                'nivel_acesso': result[3] or 0
            }
        
        return None

# Repository instances for easy import
existencias_repo = ExistenciasRepository()
pedidos_repo = PedidosRepository()
reservas_repo = ReservasRepository()
clientes_repo = ClientesRepository()
artigos_repo = ArtigosRepository()
auth_repo = AuthRepository()
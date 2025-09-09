"""
Database layer for Mobile Sales application
Centralized database connection and repository access
"""

from .connection import get_db_connection, DatabaseError
from .repositories import (
    AuthRepository, 
    ExistenciasRepository, 
    PedidosRepository, 
    ReservasRepository,
    RequisicoesRepository,
    LaboratorioRepository,
    ArtigosRepository,
    ClientesRepository,
    UserPreferencesRepository
)

# Initialize repository instances
auth_repo = AuthRepository()
existencias_repo = ExistenciasRepository()
pedidos_repo = PedidosRepository()
reservas_repo = ReservasRepository()
requisicoes_repo = RequisicoesRepository()
laboratorio_repo = LaboratorioRepository()
artigos_repo = ArtigosRepository()
clientes_repo = ClientesRepository()
user_preferences_repo = UserPreferencesRepository()

__all__ = [
    'get_db_connection',
    'DatabaseError',
    'auth_repo',
    'existencias_repo', 
    'pedidos_repo',
    'reservas_repo',
    'requisicoes_repo',
    'laboratorio_repo',
    'artigos_repo',
    'clientes_repo',
    'user_preferences_repo'
]
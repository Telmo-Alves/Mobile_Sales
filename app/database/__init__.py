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
    ArtigosRepository,
    ClientesRepository
)

# Initialize repository instances
auth_repo = AuthRepository()
existencias_repo = ExistenciasRepository()
pedidos_repo = PedidosRepository()
reservas_repo = ReservasRepository()
artigos_repo = ArtigosRepository()
clientes_repo = ClientesRepository()

__all__ = [
    'get_db_connection',
    'DatabaseError',
    'auth_repo',
    'existencias_repo', 
    'pedidos_repo',
    'reservas_repo',
    'artigos_repo',
    'clientes_repo'
]
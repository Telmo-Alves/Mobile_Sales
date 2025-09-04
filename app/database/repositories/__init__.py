"""
Repository classes for database operations
Each repository handles a specific domain
"""

from ..base import BaseRepository
from .auth import AuthRepository
from .existencias import ExistenciasRepository
from .pedidos import PedidosRepository
from .reservas import ReservasRepository
from .requisicoes import RequisicoesRepository
from .laboratorio import LaboratorioRepository
from .artigos import ArtigosRepository
from .clientes import ClientesRepository

__all__ = [
    'BaseRepository',
    'AuthRepository',
    'ExistenciasRepository', 
    'PedidosRepository',
    'ReservasRepository',
    'RequisicoesRepository',
    'LaboratorioRepository',
    'ArtigosRepository',
    'ClientesRepository'
]
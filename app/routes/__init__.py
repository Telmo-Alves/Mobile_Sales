"""
Route blueprints for Mobile Sales application
Each blueprint handles a specific functional area
"""

from .auth import auth_bp
from .dashboard import dashboard_bp
from .existencias import existencias_bp
from .pedidos import pedidos_bp
from .cotacoes import cotacoes_bp
from .api import api_bp

__all__ = [
    'auth_bp',
    'dashboard_bp', 
    'existencias_bp',
    'pedidos_bp',
    'cotacoes_bp',
    'api_bp'
]
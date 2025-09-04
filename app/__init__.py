"""
Mobile Sales Flask Application
Enhanced version with improved structure and database abstraction
"""

from flask import Flask
from datetime import timedelta
import os

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    from .config import SECRET_KEY
    app.secret_key = SECRET_KEY
    app.permanent_session_lifetime = timedelta(hours=8)
    
    # Register blueprints
    from .routes import auth_bp, dashboard_bp, existencias_bp, pedidos_bp, api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(existencias_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(api_bp)
    
    return app
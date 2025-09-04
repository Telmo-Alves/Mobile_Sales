from flask import Flask
from datetime import timedelta
from config import SECRET_KEY

# Import database abstraction layer
from app.database import (
    existencias_repo, pedidos_repo, reservas_repo, requisicoes_repo, laboratorio_repo,
    clientes_repo, artigos_repo, auth_repo
)

# Import blueprints
from app.routes import auth_bp, dashboard_bp, existencias_bp, pedidos_bp, api_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=8)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(existencias_bp)
app.register_blueprint(pedidos_bp)
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
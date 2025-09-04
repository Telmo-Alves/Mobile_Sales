"""
API routes for Mobile Sales application
"""

from flask import Blueprint, request, jsonify, session, render_template, current_app
from ..utils import login_required
from ..database import artigos_repo, reservas_repo
from ..database.connection import get_db_connection

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/search_cliente')
@login_required
def search_cliente():
    """API para pesquisar clientes (autocomplete)"""
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT FIRST 10 Cliente, Nome1, Localidade
            FROM Clientes
            WHERE Activo = 'S' 
            AND (UPPER(Nome1) LIKE UPPER(?) OR UPPER(Cliente) LIKE UPPER(?))
            ORDER BY Nome1
        """, (f'%{q}%', f'%{q}%'))
        
        results = [{'id': row[0], 'nome': row[1], 'localidade': row[2]} 
                  for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        if conn:
            conn.close()
        return jsonify([])

@api_bp.route('/reservas/<codigo>/<lote>')
@login_required
def lista_reservas(codigo, lote):
    """Lista reservas/encomendas usando ReservasRepository"""
    fornecedor = request.args.get('fornecedor', '')
    
    try:
        # Get product info using ArtigosRepository
        info_artigo = artigos_repo.get_product_info(codigo)
        if info_artigo:
            info_artigo = (codigo, info_artigo['descricao'])  # Convert to tuple format for template
        
        # Get reservations using ReservasRepository
        vendedor = session.get('cd_vend', session.get('vendedor', 0))  # Use cd_vend if available, fallback to vendedor
        reservas = reservas_repo.get_reservations(codigo, lote, fornecedor, vendedor)
        
        return render_template('reservas.html', 
                             reservas=reservas,
                             info_artigo=info_artigo,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor)
                             
    except Exception as e:
        current_app.logger.error(f"Erro na consulta de reservas: {str(e)}")
        return render_template('reservas.html', 
                             reservas=[],
                             info_artigo=None,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor,
                             error=f'Erro ao consultar reservas: {str(e)}')
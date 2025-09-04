"""
Exemplo de como o app.py ficaria refatorado usando a camada de abstração
Este é um exemplo para demonstração - não substitui o app.py atual
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta
from functools import wraps
from database import (
    existencias_repo, pedidos_repo, reservas_repo, 
    clientes_repo, artigos_repo, auth_repo
)
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-flask-mobile-sales'
app.permanent_session_lifetime = timedelta(hours=8)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login_required(f):
    """Decorator para routes que requerem login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'validar' not in session or session['validar'] != 1:
            return redirect(url_for('login'))
        
        # Check session timeout (8 hours)
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > timedelta(hours=8):
                session.clear()
                flash('Sessão expirou. Por favor, faça login novamente.', 'warning')
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login refatorado usando AuthRepository"""
    if request.method == 'POST':
        user_input = request.form.get('user', '').strip()
        password = request.form.get('password', '').strip()
        
        if not user_input or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')
        
        # Convert user format (01 -> U01)
        if user_input.isdigit():
            utilizador_busca = f'U{user_input.zfill(2)}'
        else:
            utilizador_busca = user_input.upper()
        
        try:
            # Use AuthRepository instead of direct DB calls
            user_data = auth_repo.authenticate_user(utilizador_busca, password)
            
            if user_data:
                session.permanent = True
                session['user'] = utilizador_busca
                session['vendedor'] = user_data['vendedor']
                session['nivel_acesso'] = user_data['nivel_acesso']
                session['validar'] = 1
                session['login_time'] = datetime.now().isoformat()
                
                logger.info(f"Login successful: {utilizador_busca}, Vendedor: {user_data['vendedor']}, Nível: {user_data['nivel_acesso']}")
                return redirect(url_for('dashboard'))
            else:
                flash('Credenciais inválidas.', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('Erro interno. Tente novamente.', 'error')
    
    return render_template('login.html')

@app.route('/existencias/consulta', methods=['POST'])
@login_required
def existencias_consulta():
    """Consulta de existências refatorada usando ExistenciasRepository"""
    codigo_artigo = request.form.get('codigo_artigo', '').strip()
    
    if not codigo_artigo:
        flash('Por favor, insira um código de artigo.', 'warning')
        return redirect(url_for('existencias'))
    
    try:
        # Use ExistenciasRepository instead of direct DB calls
        enc_forn = session.get('enc_forn', 'S')
        resultados = existencias_repo.search_products(codigo_artigo, enc_forn)
        
        if resultados:
            flash(f'Encontrados {len(resultados)} resultados para "{codigo_artigo}".', 'success')
        else:
            flash(f'Nenhum resultado encontrado para "{codigo_artigo}".', 'info')
            
        return render_template('existencias_resultado.html', 
                             resultados=resultados,
                             codigo_pesquisado=codigo_artigo)
                             
    except Exception as e:
        logger.error(f"Erro na consulta de existências: {str(e)}")
        flash(f'Erro na consulta: {str(e)}', 'error')
        return redirect(url_for('existencias'))

@app.route('/detalhes_lote/<codigo>')
@login_required
def detalhes_lote(codigo):
    """Detalhes do lote refatorados usando ExistenciasRepository"""
    try:
        enc_forn = session.get('enc_forn', 'S')
        
        # Use ExistenciasRepository for both main data and lab results
        lotes_data = existencias_repo.get_product_details(codigo, enc_forn)
        
        # Process lab results for each lot
        for lote_info in lotes_data:
            lote = lote_info[1]  # RLote
            lab_results = existencias_repo.get_lab_results(codigo, lote)
            lote_info.append(lab_results)  # Add lab results to the tuple
        
        nivel_acesso = session.get('nivel_acesso', 0)
        
        return render_template('_detalhes_lote_partial.html', 
                             lotes_data=lotes_data,
                             codigo=codigo,
                             nivel_acesso=nivel_acesso)
                             
    except Exception as e:
        logger.error(f"Erro nos detalhes do lote: {str(e)}")
        return f"<p class='text-danger'>Erro ao carregar detalhes: {str(e)}</p>"

@app.route('/pedidos')
@login_required
def pedidos():
    """Lista de pedidos refatorada usando PedidosRepository"""
    try:
        vendedor = session.get('vendedor', 0)
        
        # Use PedidosRepository instead of direct DB calls
        pedidos_data = pedidos_repo.get_orders_list(vendedor)
        
        # Convert to list of dicts for easier template use
        columns = ['Pedido', 'Quantidade', 'Preco', 'Lote', 'Descricao', 'Cliente', 'Estado', 'Dt_Registo']
        pedidos_list = [dict(zip(columns, row)) for row in pedidos_data]
        
        return render_template('pedidos.html', pedidos=pedidos_list)
        
    except Exception as e:
        logger.error(f"Erro ao carregar pedidos: {str(e)}")
        flash(f'Erro ao carregar pedidos: {str(e)}', 'warning')
        return render_template('pedidos.html', pedidos=[])

@app.route('/anular_pedido', methods=['POST'])
@login_required
def anular_pedido():
    """Anular pedido refatorado usando PedidosRepository"""
    pedido_num = request.form.get('pedido')
    
    if not pedido_num:
        return jsonify({'success': False, 'error': 'Número do pedido não fornecido'})
    
    try:
        pedido_num = int(pedido_num)
        vendedor = session.get('vendedor', 0)
        
        # Use PedidosRepository for cancellation logic
        result = pedidos_repo.cancel_order(pedido_num, vendedor)
        
        if result['success']:
            logger.info(f"Pedido {pedido_num} anulado por utilizador {session.get('user')}")
        
        return jsonify(result)
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Número do pedido inválido'})
    except Exception as e:
        logger.error(f"Erro ao anular pedido {pedido_num}: {str(e)}")
        return jsonify({'success': False, 'error': f'Erro ao anular pedido: {str(e)}'})

@app.route('/reservas/<codigo>/<lote>')
@login_required  
def lista_reservas(codigo, lote):
    """Lista reservas refatorada usando ReservasRepository"""
    fornecedor = request.args.get('fornecedor', '')
    
    try:
        # Get product info
        info_artigo = artigos_repo.get_product_info(codigo)
        
        # Get reservations using repository
        vendedor = session.get('vendedor', 0)  # Note: should be 'cd_vend' in original
        reservas = reservas_repo.get_reservations(codigo, lote, fornecedor, vendedor)
        
        return render_template('reservas.html', 
                             reservas=reservas,
                             info_artigo=info_artigo,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor)
                             
    except Exception as e:
        logger.error(f"Erro na consulta de reservas: {str(e)}")
        flash(f'Erro ao consultar reservas: {str(e)}', 'error')
        return render_template('reservas.html', 
                             reservas=[],
                             info_artigo=None,
                             codigo=codigo, 
                             lote=lote,
                             fornecedor=fornecedor)

@app.route('/registar_pedido', methods=['POST'])
@login_required
def registar_pedido():
    """Registo de pedido refatorado usando PedidosRepository"""
    pedido_validado = session.get('pedido_validado')
    
    if not pedido_validado:
        flash('Pedido não encontrado. Por favor, tente novamente.', 'error')
        return redirect(url_for('existencias'))
    
    try:
        # Add vendor info to order data
        pedido_validado['vendedor'] = session.get('vendedor', 0)
        
        # Use PedidosRepository to create order
        success = pedidos_repo.create_order(pedido_validado)
        
        if success:
            # Clear session data
            session.pop('pedido_dados', None)
            session.pop('pedido_validado', None)
            
            flash(f'REGISTO INTRODUZIDO COM SUCESSO! Código: {pedido_validado["codigo"]}, Lote: {pedido_validado["lote"]}, Quantidade: {pedido_validado["quantidade"]:.2f}', 'success')
            logger.info(f"Pedido criado com sucesso para utilizador {session.get('user')}")
        else:
            flash('Erro ao registar pedido. Tente novamente.', 'error')
            
    except Exception as e:
        logger.error(f"Erro no registo de pedido: {str(e)}")
        flash(f'Erro ao registar pedido: {str(e)}', 'error')
    
    return redirect(url_for('existencias'))

# Exemplo de como usar o contexto do cursor para operações mais complexas
@app.route('/exemplo_transacao')
@login_required
def exemplo_transacao():
    """Exemplo de operação com transação usando context manager"""
    try:
        from database import db
        
        with db.get_cursor(auto_commit=True) as cursor:
            # Múltiplas operações numa transação
            cursor.execute("INSERT INTO tabela1 VALUES (?, ?)", (1, 'teste'))
            cursor.execute("UPDATE tabela2 SET campo = ? WHERE id = ?", ('novo_valor', 123))
            # Se qualquer operação falhar, rollback automático
            # Se todas passarem, commit automático
            
        return jsonify({'success': True, 'message': 'Transação concluída'})
        
    except Exception as e:
        logger.error(f"Erro na transação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
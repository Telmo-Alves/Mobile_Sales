"""
Order management routes for Mobile Sales application
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from ..utils import login_required
from ..database import pedidos_repo
from ..database.connection import get_db_connection

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/pedidos')
@login_required
def pedidos():
    """Lista de pedidos usando PedidosRepository"""
    pedidos_list = []
    
    try:
        vendedor = session.get('vendedor', 0)
        
        # Use PedidosRepository for orders list
        pedidos_data = pedidos_repo.get_orders_list(vendedor)
        
        # Convert to list of dicts for template use - using uppercase keys to match template
        columns = ['PEDIDO', 'QUANTIDADE', 'PRECO', 'LOTE', 'DESCRICAO', 'CLIENTE', 'ESTADO', 'DT_REGISTO']
        pedidos_list = [dict(zip(columns, row)) for row in pedidos_data]
        
    except Exception as e:
        flash(f'Erro ao carregar pedidos: {str(e)}', 'warning')
        current_app.logger.error(f"Erro ao carregar pedidos: {str(e)}")
    
    return render_template('pedidos.html', pedidos=pedidos_list)

@pedidos_bp.route('/anular_pedido', methods=['POST'])
@login_required
def anular_pedido():
    """Anular um pedido usando PedidosRepository"""
    pedido_num = request.form.get('pedido')
    
    if not pedido_num:
        return jsonify({'success': False, 'error': 'Número do pedido não fornecido'})
    
    try:
        pedido_num = int(pedido_num)
        vendedor = session.get('vendedor', 0)
        
        # Use PedidosRepository for cancellation logic
        result = pedidos_repo.cancel_order(pedido_num, vendedor)
        
        if result['success']:
            current_app.logger.info(f"Pedido {pedido_num} anulado por utilizador {session.get('user')}")
        
        return jsonify(result)
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Número do pedido inválido'})
    except Exception as e:
        current_app.logger.error(f"Erro ao anular pedido {pedido_num}: {str(e)}")
        return jsonify({'success': False, 'error': f'Erro ao anular pedido: {str(e)}'})

@pedidos_bp.route('/novo_pedido', methods=['GET', 'POST'])
@login_required
def novo_pedido():
    """Criar novo pedido"""
    if request.method == 'POST':
        # Aqui implementaria a lógica para gravar o pedido
        flash('Funcionalidade em desenvolvimento', 'info')
        return redirect(url_for('pedidos.pedidos'))
    
    # Carregar dados necessários para o formulário
    clientes_list = []
    artigos_list = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar clientes
            cursor.execute("""
                SELECT Cliente, Nome1 FROM Clientes 
                WHERE Activo = 'S' ORDER BY Nome1
            """)
            clientes_list = cursor.fetchall()
            
            # Buscar artigos
            cursor.execute("""
                SELECT Codigo, Descricao, P_Venda1 FROM Artigos 
                WHERE Activo = 'S' ORDER BY Descricao
            """)
            artigos_list = cursor.fetchall()
            
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar dados: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('novo_pedido.html', 
                         clientes=clientes_list, 
                         artigos=artigos_list)

@pedidos_bp.route('/pedido')
@login_required
def pedido():
    """Formulário para criar pedido de artigo/lote"""
    codigo = request.args.get('codigo', '')
    lote = request.args.get('lote', '')
    armazem = request.args.get('armazem', '')
    preco = request.args.get('preco', '')
    quant = request.args.get('quant', '')
    obs = request.args.get('obs', '')
    
    # Import config here to avoid circular imports
    from config import WAREHOUSE_CONFIG
    
    # Dados do produto
    produto_info = {}
    quantidade_disponivel = 0
    precos_produto = {'p_qt1': 0, 'p_qt2': 0}
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar informações do produto
            cursor.execute("SELECT Descricao, P_Qt1, P_Qt2 FROM Artigos WHERE Codigo = ?", (codigo,))
            produto = cursor.fetchone()
            if produto:
                produto_info = {
                    'codigo': codigo,
                    'descricao': produto[0],
                    'preco_base': produto[1] or 0,
                    'preco_alt': produto[2] or 0
                }
                precos_produto = {'p_qt1': produto[1] or 0, 'p_qt2': produto[2] or 0}
            
            # Buscar quantidade disponível do lote específico - usando configurações de armazém
            if lote:
                arm_ini = WAREHOUSE_CONFIG.get('arm_ini', 1)
                arm_fim = WAREHOUSE_CONFIG.get('arm_fim', 999)
                
                cursor.execute("""
                    SELECT (RExist - REncCli + REncFor) as RStkDisp 
                    FROM Inq_Exist_Lote_Pda_2(?, ?, ?, ?, 'ACT', 0, '31.12.3000', ?, '31.12.3000', 0, 'S', 1, 2, 2)
                    WHERE RLote = ?
                """, (codigo, codigo, arm_ini, arm_fim, session.get('enc_forn', 'S'), lote))
                resultado = cursor.fetchone()
                if resultado and resultado[0] > 0:
                    quantidade_disponivel = resultado[0]
            
            # Buscar preços específicos para o lote (se existirem)
            cursor.execute("SELECT Preco1, Preco2 FROM RelArtLote_Preco WHERE Codigo = ? AND Lote = ?", (codigo, lote))
            preco_lote = cursor.fetchone()
            if preco_lote:
                precos_produto['rel_p_qt1'] = preco_lote[0] or 0
                precos_produto['rel_p_qt2'] = preco_lote[1] or 0
            
            # Buscar lista de clientes do vendedor
            vendedor = session.get('vendedor', session.get('cd_vend', ''))
            cursor.execute("""
                SELECT l.cliente, l.Nome1, c.Situacao, rc2.vendedor
                FROM Locais_Entrega l
                LEFT OUTER JOIN clientes c ON c.cliente = l.cliente
                LEFT OUTER JOIN Rel_Cli_Vend2 rc2 ON rc2.cliente = l.cliente
                WHERE (c.situacao IN ('ACT', 'MANUT'))
                AND ((l.vendedor = ?) OR (rc2.vendedor = ?) OR (? = 1))
                ORDER BY l.Nome1
            """, (vendedor, vendedor, vendedor))
            clientes = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao carregar dados do pedido: {str(e)}', 'error')
            if conn:
                conn.close()
            clientes = []
    
    # Definir valores padrão se não fornecidos
    if not preco and produto_info:
        preco = precos_produto.get('rel_p_qt1') or precos_produto.get('p_qt1') or 0
    
    if not quant or float(quant or 0) <= 0:
        quant = quantidade_disponivel
    
    # Armazenar dados na sessão para o processamento
    session['pedido_dados'] = {
        'codigo': codigo,
        'armazem': armazem,
        'obs': obs,
        'descricao': produto_info.get('descricao', ''),
        'existencia': quantidade_disponivel,
        'p_qt1': precos_produto.get('p_qt1', 0),
        'p_qt2': precos_produto.get('p_qt2', 0),
        'rel_p_qt1': precos_produto.get('rel_p_qt1', 0),
        'rel_p_qt2': precos_produto.get('rel_p_qt2', 0)
    }
    
    return render_template('pedido.html',
                         produto=produto_info,
                         lote=lote,
                         preco=float(preco or 0),
                         quantidade=float(quant or 0),
                         quantidade_disponivel=quantidade_disponivel,
                         clientes=clientes,
                         obs=obs)

@pedidos_bp.route('/validapedido', methods=['POST'])
@login_required
def validar_pedido():
    """Validar pedido antes da criação"""
    # Import config here to avoid circular imports
    from config import WAREHOUSE_CONFIG
    
    dados = request.form.to_dict()
    pedido_dados = session.get('pedido_dados', {})
    
    # Extrair dados do formulário
    codigo = pedido_dados.get('codigo', '')
    armazem = pedido_dados.get('armazem', '')
    lote = dados.get('Lote', '')
    cliente = dados.get('Cliente', '')
    preco = float(dados.get('Preco', '0').replace(',', '.'))
    quantidade = float(dados.get('Quantidade', '0').replace('.', '').replace(',', '.'))
    entrega = dados.get('Entrega', '')
    local_entrega = dados.get('LocalEntrega', '')
    obs = dados.get('Obs', '')
    obs2 = dados.get('Obs2', '')
    
    # Inicializar variáveis de validação
    validacoes = {
        'plafond_ultrapassado': False,
        'lote_em_branco': False,
        'lote_inexistente': False,
        'stock_indisponivel': False,
        'preco_fora_tabela': False,
        'quantidade_invalida': False,
        'pode_validar': True
    }
    
    dados_validacao = {
        'cliente_nome': '',
        'produto_descricao': pedido_dados.get('descricao', ''),
        'plafond': 0,
        'plafond_usado': 0,
        'valor_encomenda': preco * quantidade,
        'existencia': 0,
        'preco_min': pedido_dados.get('rel_p_qt2', 0) or pedido_dados.get('p_qt2', 0),
        'preco_max': pedido_dados.get('rel_p_qt1', 0) or pedido_dados.get('p_qt1', 0)
    }
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            debug_info = []
            
            # 1. Buscar dados do cliente - SIMPLIFICADO
            try:
                sql_cliente = "SELECT Nome1 FROM Locais_Entrega WHERE Cliente = ? AND local_id = ?"
                params_cliente = (str(cliente), 'SEDE')
                debug_info.append(f"1. SQL Cliente: {sql_cliente} | Params: {params_cliente}")
                cursor.execute(sql_cliente, params_cliente)
                cliente_row = cursor.fetchone()
                if cliente_row:
                    dados_validacao['cliente_nome'] = cliente_row[0]
                    debug_info.append(f"1. Cliente encontrado: {cliente_row[0]}")
                else:
                    debug_info.append("1. Cliente não encontrado")
            except Exception as e1:
                debug_info.append(f"1. ERRO Cliente: {str(e1)}")
                raise e1
            
            # 2. PULAR Validação de Plafond por enquanto para isolar o problema
            debug_info.append("2. Plafond: PULADO para debug")
            
            # 3. Validar Lote - SIMPLIFICADO
            if not lote or len(lote.strip()) == 0:
                validacoes['lote_em_branco'] = True
                debug_info.append("3. Lote em branco")
            else:
                try:
                    sql_lote = "SELECT Lote FROM Lotes WHERE Lote = ?"
                    params_lote = (str(lote),)
                    debug_info.append(f"3. SQL Lote: {sql_lote} | Params: {params_lote}")
                    cursor.execute(sql_lote, params_lote)
                    lote_row = cursor.fetchone()
                    if not lote_row:
                        validacoes['lote_inexistente'] = True
                        validacoes['pode_validar'] = False
                        debug_info.append("3. Lote não encontrado")
                    else:
                        debug_info.append(f"3. Lote encontrado: {lote_row[0]}")
                        
                        # 4. SIMPLIFICAR query de stock - usando configurações de armazém
                        try:
                            arm_ini = WAREHOUSE_CONFIG.get('arm_ini', 1)
                            arm_fim = WAREHOUSE_CONFIG.get('arm_fim', 999)
                            
                            # Tentar query mais simples primeiro
                            sql_stock_simples = """
                                SELECT RExist, REncCli, REncFor, (RExist - REncCli + REncFor) as RStkDisp
                                FROM Inq_Exist_Lote_Pda_2(?, ?, ?, ?, 'ACT', 0, '31.12.3000', ?, '31.12.3000', 0, 'S', 1, 2, 2)
                                WHERE RLote = ?
                            """
                            params_stock = (str(codigo), str(codigo), arm_ini, arm_fim, str(session.get('enc_forn', 'S')), str(lote))
                            debug_info.append(f"4. SQL Stock: {sql_stock_simples} | Params: {params_stock}")
                            cursor.execute(sql_stock_simples, params_stock)
                            stock_row = cursor.fetchone()
                            if stock_row:
                                dados_validacao['existencia'] = stock_row[3] or 0  # RStkDisp
                                debug_info.append(f"4. Stock encontrado - Exist:{stock_row[0]}, Enc:{stock_row[1]}, Disp:{stock_row[3]}")
                                if dados_validacao['existencia'] < quantidade:
                                    validacoes['stock_indisponivel'] = True
                            else:
                                debug_info.append("4. Stock não encontrado")
                        except Exception as e4:
                            debug_info.append(f"4. ERRO Stock: {str(e4)}")
                            raise e4
                except Exception as e3:
                    debug_info.append(f"3. ERRO Lote: {str(e3)}")
                    raise e3
            
            # 5. Validar Preço
            debug_info.append(f"5. Preços - Min:{dados_validacao['preco_min']}, Max:{dados_validacao['preco_max']}, Atual:{preco}")
            if dados_validacao['preco_max'] > 0 and dados_validacao['preco_min'] > 0:
                if preco > dados_validacao['preco_max'] or preco < dados_validacao['preco_min']:
                    validacoes['preco_fora_tabela'] = True
                    debug_info.append("5. Preço fora da tabela")
                    if preco == 0:
                        validacoes['pode_validar'] = False
                        debug_info.append("5. Preço zero - não validável")
            
            # 6. Validar Quantidade
            debug_info.append(f"6. Quantidade: {quantidade}")
            if quantidade <= 0:
                validacoes['quantidade_invalida'] = True
                validacoes['pode_validar'] = False
                debug_info.append("6. Quantidade inválida")
            
            # 7. Verificar permissões do usuário
            debug_info.append(f"7. Usuário: {session.get('user', 'N/A')}")
            if session.get('user') == 'U99':
                validacoes['pode_validar'] = False
                debug_info.append("7. Usuário U99 - não pode validar")
            
            # Log completo do debug
            current_app.logger.info(f"DEBUG Validação Completa: {debug_info}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            # Log detalhado do erro com informações de debug
            error_details = {
                'error': str(e),
                'codigo': codigo,
                'lote': lote,
                'cliente': cliente,
                'vendedor': session.get('vendedor', session.get('cd_vend', '')),
                'enc_forn': session.get('enc_forn', 'S'),
                'user': session.get('user', 'N/A'),
                'debug_steps': debug_info if 'debug_info' in locals() else []
            }
            current_app.logger.error(f"ERRO DETALHADO na validação: {error_details}")
            flash(f'Erro na validação (passo {len(debug_info) if "debug_info" in locals() else "?"}): {str(e)}', 'error')
            if conn:
                conn.close()
            return redirect(url_for('existencias.existencias'))
    
    # Armazenar dados para possível criação do pedido
    if validacoes['pode_validar']:
        session['pedido_validado'] = {
            'codigo': codigo,
            'armazem': armazem,
            'lote': lote,
            'cliente': cliente,
            'preco': preco,
            'quantidade': quantidade,
            'entrega': entrega,
            'local_entrega': local_entrega,
            'obs': obs,
            'obs2': obs2,
            'avisos': f"{int(validacoes['plafond_ultrapassado'])}{int(validacoes['lote_em_branco'])}{int(validacoes['lote_inexistente'])}{int(validacoes['stock_indisponivel'])}{int(validacoes['preco_fora_tabela'])}00"
        }
    
    return render_template('validapedido.html',
                         validacoes=validacoes,
                         dados=dados_validacao,
                         pedido={
                             'codigo': codigo,
                             'lote': lote,
                             'cliente': cliente,
                             'preco': preco,
                             'quantidade': quantidade
                         })

@pedidos_bp.route('/registapedido', methods=['POST'])
@login_required 
def registar_pedido():
    """Registar o pedido usando PedidosRepository"""
    pedido_validado = session.get('pedido_validado')
    
    if not pedido_validado:
        flash('Pedido não encontrado. Por favor, tente novamente.', 'error')
        return redirect(url_for('existencias.existencias'))
    
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
            current_app.logger.info(f"Pedido criado com sucesso para utilizador {session.get('user')}")
        else:
            flash('Erro ao registar pedido. Tente novamente.', 'error')
            
    except Exception as e:
        current_app.logger.error(f"Erro no registo de pedido: {str(e)}")
        flash(f'Erro ao registar pedido: {str(e)}', 'error')
    
    return redirect(url_for('existencias.existencias'))
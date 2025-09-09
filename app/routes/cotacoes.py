"""
Quotation management routes for Mobile Sales application
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from ..utils import login_required
from ..database.connection import get_db_connection
from datetime import datetime

cotacoes_bp = Blueprint('cotacoes', __name__)

@cotacoes_bp.route('/cotacoes')
@login_required
def cotacoes():
    """Lista de cotações"""
    cotacoes_list = []
    
    try:
        vendedor = session.get('vendedor', 0)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Buscar cotações do vendedor
            cursor.execute("""
                SELECT c.Id, c.Cliente, c.Nome_Cliente, c.Data_Criacao, c.Data_Validade,
                       c.Status, c.Valor_Total, c.Observacoes,
                       COUNT(ci.Id) as Num_Itens
                FROM Cotacoes c
                LEFT JOIN Cotacoes_Itens ci ON c.Id = ci.Cotacao_Id
                WHERE c.Vendedor = ? 
                ORDER BY c.Data_Criacao DESC
            """, (vendedor,))
            
            cotacoes_data = cursor.fetchall()
            
            # Convert to list of dicts for template use
            columns = ['ID', 'CLIENTE', 'NOME_CLIENTE', 'DATA_CRIACAO', 'DATA_VALIDADE', 
                      'STATUS', 'VALOR_TOTAL', 'OBSERVACOES', 'NUM_ITENS']
            cotacoes_list = [dict(zip(columns, row)) for row in cotacoes_data]
            
            cursor.close()
            conn.close()
        
    except Exception as e:
        flash(f'Erro ao carregar cotações: {str(e)}', 'warning')
        current_app.logger.error(f"Erro ao carregar cotações: {str(e)}")
    
    return render_template('cotacoes.html', cotacoes=cotacoes_list)

@cotacoes_bp.route('/nova_cotacao', methods=['GET', 'POST'])
@login_required
def nova_cotacao():
    """Criar nova cotação"""
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            vendedor = session.get('vendedor', 0)
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Inserir nova cotação
                cursor.execute("""
                    INSERT INTO Cotacoes (Cliente, Nome_Cliente, Data_Criacao, Data_Validade,
                                        Status, Valor_Total, Observacoes, Vendedor)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?, 'PENDENTE', 0, ?, ?)
                """, (
                    data.get('cliente'),
                    data.get('nome_cliente'),
                    data.get('data_validade'),
                    data.get('observacoes', ''),
                    vendedor
                ))
                
                cotacao_id = cursor.lastrowid
                conn.commit()
                cursor.close()
                conn.close()
                
                flash(f'Cotação #{cotacao_id} criada com sucesso!', 'success')
                return redirect(url_for('cotacoes.editar_cotacao', id=cotacao_id))
        
        except Exception as e:
            flash(f'Erro ao criar cotação: {str(e)}', 'error')
            current_app.logger.error(f"Erro ao criar cotação: {str(e)}")
    
    # Carregar lista de clientes para o formulário
    clientes_list = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            vendedor = session.get('vendedor', session.get('cd_vend', ''))
            
            cursor.execute("""
                SELECT l.cliente, l.Nome1
                FROM Locais_Entrega l
                LEFT OUTER JOIN clientes c ON c.cliente = l.cliente
                LEFT OUTER JOIN Rel_Cli_Vend2 rc2 ON rc2.cliente = l.cliente
                WHERE (c.situacao IN ('ACT', 'MANUT'))
                AND ((l.vendedor = ?) OR (rc2.vendedor = ?) OR (? = 1))
                ORDER BY l.Nome1
            """, (vendedor, vendedor, vendedor))
            
            clientes_list = cursor.fetchall()
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao carregar clientes: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('nova_cotacao.html', clientes=clientes_list)

@cotacoes_bp.route('/editar_cotacao/<int:id>')
@login_required
def editar_cotacao(id):
    """Editar cotação existente"""
    cotacao = None
    itens = []
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar dados da cotação
            cursor.execute("""
                SELECT Id, Cliente, Nome_Cliente, Data_Criacao, Data_Validade,
                       Status, Valor_Total, Observacoes
                FROM Cotacoes
                WHERE Id = ? AND Vendedor = ?
            """, (id, session.get('vendedor', 0)))
            
            cotacao_data = cursor.fetchone()
            if cotacao_data:
                columns = ['ID', 'CLIENTE', 'NOME_CLIENTE', 'DATA_CRIACAO', 'DATA_VALIDADE',
                          'STATUS', 'VALOR_TOTAL', 'OBSERVACOES']
                cotacao = dict(zip(columns, cotacao_data))
                
                # Buscar itens da cotação
                cursor.execute("""
                    SELECT Id, Codigo, Descricao, Lote, Quantidade, Preco_Unitario,
                           Valor_Total, Observacoes
                    FROM Cotacoes_Itens
                    WHERE Cotacao_Id = ?
                    ORDER BY Id
                """, (id,))
                
                itens_data = cursor.fetchall()
                columns_itens = ['ID', 'CODIGO', 'DESCRICAO', 'LOTE', 'QUANTIDADE',
                               'PRECO_UNITARIO', 'VALOR_TOTAL', 'OBSERVACOES']
                itens = [dict(zip(columns_itens, row)) for row in itens_data]
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao carregar cotação: {str(e)}', 'error')
            if conn:
                conn.close()
    
    if not cotacao:
        flash('Cotação não encontrada', 'error')
        return redirect(url_for('cotacoes.cotacoes'))
    
    return render_template('editar_cotacao.html', cotacao=cotacao, itens=itens)

@cotacoes_bp.route('/adicionar_item_cotacao', methods=['POST'])
@login_required
def adicionar_item_cotacao():
    """Adicionar item à cotação"""
    try:
        data = request.form.to_dict()
        cotacao_id = int(data.get('cotacao_id'))
        codigo = data.get('codigo')
        descricao = data.get('descricao')
        lote = data.get('lote')
        quantidade = float(data.get('quantidade', 0))
        preco = float(data.get('preco', 0))
        valor_total = quantidade * preco
        observacoes = data.get('observacoes', '')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Inserir item
            cursor.execute("""
                INSERT INTO Cotacoes_Itens (Cotacao_Id, Codigo, Descricao, Lote, 
                                          Quantidade, Preco_Unitario, Valor_Total, Observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cotacao_id, codigo, descricao, lote, quantidade, preco, valor_total, observacoes))
            
            # Atualizar valor total da cotação
            cursor.execute("""
                UPDATE Cotacoes 
                SET Valor_Total = (
                    SELECT SUM(Valor_Total) FROM Cotacoes_Itens WHERE Cotacao_Id = ?
                )
                WHERE Id = ?
            """, (cotacao_id, cotacao_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Item adicionado com sucesso'})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao adicionar item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@cotacoes_bp.route('/remover_item_cotacao', methods=['POST'])
@login_required
def remover_item_cotacao():
    """Remover item da cotação"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Buscar cotacao_id antes de remover
            cursor.execute("SELECT Cotacao_Id FROM Cotacoes_Itens WHERE Id = ?", (item_id,))
            result = cursor.fetchone()
            
            if result:
                cotacao_id = result[0]
                
                # Remover item
                cursor.execute("DELETE FROM Cotacoes_Itens WHERE Id = ?", (item_id,))
                
                # Atualizar valor total da cotação
                cursor.execute("""
                    UPDATE Cotacoes 
                    SET Valor_Total = COALESCE((
                        SELECT SUM(Valor_Total) FROM Cotacoes_Itens WHERE Cotacao_Id = ?
                    ), 0)
                    WHERE Id = ?
                """, (cotacao_id, cotacao_id))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                return jsonify({'success': True, 'message': 'Item removido com sucesso'})
            else:
                return jsonify({'success': False, 'error': 'Item não encontrado'})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao remover item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@cotacoes_bp.route('/atualizar_status_cotacao', methods=['POST'])
@login_required
def atualizar_status_cotacao():
    """Atualizar status da cotação"""
    try:
        data = request.get_json()
        cotacao_id = data.get('cotacao_id')
        novo_status = data.get('status')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE Cotacoes 
                SET Status = ?
                WHERE Id = ? AND Vendedor = ?
            """, (novo_status, cotacao_id, session.get('vendedor', 0)))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Status atualizado com sucesso'})
    
    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
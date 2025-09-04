"""
Stock/inventory routes for Mobile Sales application
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from ..utils import login_required
from ..database import existencias_repo, laboratorio_repo
from ..database.connection import get_db_connection

existencias_bp = Blueprint('existencias', __name__)

def formar_codigo_artigo(tipo_art, tipo_ne, n_cabos, composicao, tipo_processo, utilizacao):
    """Forma o código do artigo baseado nos parâmetros - replica formacodigo.php"""
    
    # Casos especiais
    if tipo_art == 'F':
        return 'F'
    
    if tipo_art == 'Y':
        return 'Y'
    
    # Formar código normal
    if tipo_processo == '*':
        # Todos os processos
        codigo = f"{tipo_art}{tipo_ne}{n_cabos}{composicao}"
    else:
        # Processo específico
        utiliza = utilizacao or ''
        
        # Regras específicas de utilização
        if utilizacao == 'M' and int(n_cabos) > 1:
            utiliza = 'N'
        
        if tipo_processo == 'T' and utilizacao == 'M':
            utiliza = 'C'
        
        if tipo_processo == 'T' and utilizacao == 'T':
            utiliza = ''
        
        if tipo_processo == 'E':
            utiliza = ''
        
        codigo = f"{tipo_art}{tipo_ne}{n_cabos}{composicao}{tipo_processo}{utiliza}"
    
    return codigo

@existencias_bp.route('/existencias')
@login_required
def existencias():
    """Página de consulta de existências/stock"""
    
    # Recuperar filtros guardados na sessão (se existirem)
    filtros_guardados = {
        'tipo_artigo': session.get('filtro_tipo_artigo', ''),
        'tipo_ne': session.get('filtro_tipo_ne', ''),
        'n_cabos': session.get('filtro_n_cabos', ''),
        'composicao': session.get('filtro_composicao', ''),
        'tipo_processo': session.get('filtro_tipo_processo', '*'),
        'enc_forn': session.get('filtro_enc_forn', 'S'),
        'utilizacao': session.get('filtro_utilizacao', '')
    }
    
    # Dados para os dropdowns
    tipo_artigo = []
    tipo_ne = []
    n_cabos = []
    composicoes = []
    tipo_processo = []
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar Tipo de Artigo (Posição 1)
            cursor.execute("""
                SELECT CTV.Valor, CTV.Descricao, CTV.ID
                FROM Forma_Codigo FC
                LEFT OUTER JOIN codigo_tabelas CT ON CT.ID = FC.Tab_Ref
                LEFT OUTER JOIN codigo_tab_valores CTV ON CTV.Tab_ID = CT.ID AND CTV.Activo = 1
                WHERE FC.Posicao = 1
                ORDER BY CTV.Descricao
            """)
            tipo_artigo = cursor.fetchall()
            
            # Buscar Tipo NE (Posição 2)
            cursor.execute("""
                SELECT CTV.Valor, CTV.Descricao, CTV.ID
                FROM Forma_Codigo FC
                LEFT OUTER JOIN codigo_tabelas CT ON CT.ID = FC.Tab_Ref
                LEFT OUTER JOIN codigo_tab_valores CTV ON CTV.Tab_ID = CT.ID AND CTV.Activo = 1
                WHERE FC.Posicao = 2
                ORDER BY CTV.Descricao
            """)
            tipo_ne = cursor.fetchall()
            
            # Buscar Número de Cabos (Posição 5)
            cursor.execute("""
                SELECT CTV.Valor, CTV.Descricao, CTV.ID
                FROM Forma_Codigo FC
                LEFT OUTER JOIN codigo_tabelas CT ON CT.ID = FC.Tab_Ref
                LEFT OUTER JOIN codigo_tab_valores CTV ON CTV.Tab_ID = CT.ID AND CTV.Activo = 1
                WHERE FC.Posicao = 5
                ORDER BY CTV.Descricao
            """)
            n_cabos = cursor.fetchall()
            
            # Buscar Composições
            cursor.execute("""
                SELECT CodArt, Desc_Pda, Composicao 
                FROM Rel_Comp_CodArt 
                WHERE Char_Length(Trim(Desc_Pda)) > 2 AND listar = 'S' 
                ORDER BY Desc_Pda
            """)
            composicoes = cursor.fetchall()
            
            # Buscar Tipos de Processo
            cursor.execute("""
                SELECT Tipo, Descricao 
                FROM Tipo_Processo 
                ORDER BY Descricao
            """)
            tipo_processo = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao carregar dados: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('existencias.html',
                         tipo_artigo=tipo_artigo,
                         tipo_ne=tipo_ne,
                         n_cabos=n_cabos,
                         composicoes=composicoes,
                         tipo_processo=tipo_processo,
                         filtros_guardados=filtros_guardados)

@existencias_bp.route('/existencias/consulta', methods=['POST'])
@login_required
def existencias_consulta():
    """Consultar existências com os filtros selecionados"""
    
    # Obter parâmetros do formulário
    tipo_art = request.form.get('tipo_artigo', '')
    tipo_ne = request.form.get('tipo_ne', '')
    n_cabos = request.form.get('n_cabos', '')
    enc_forn = request.form.get('enc_forn', 'S')
    composicao = request.form.get('composicao', '')
    tipo_processo = request.form.get('tipo_processo', '*')
    utilizacao = request.form.get('utilizacao', '')
    action = request.form.get('action', 'consultar')
    
    # Guardar filtros na sessão para reutilização
    session['filtro_tipo_artigo'] = tipo_art
    session['filtro_tipo_ne'] = tipo_ne
    session['filtro_n_cabos'] = n_cabos
    session['filtro_composicao'] = composicao
    session['filtro_tipo_processo'] = tipo_processo
    session['filtro_enc_forn'] = enc_forn
    session['filtro_utilizacao'] = utilizacao
    
    # Formar código do artigo
    codigo_artigo = formar_codigo_artigo(tipo_art, tipo_ne, n_cabos, composicao, tipo_processo, utilizacao)
    
    # Guardar na sessão para uso posterior
    session['ultimo_codigo_pesquisa'] = codigo_artigo
    session['enc_forn'] = enc_forn
    session['tipo_processo'] = tipo_processo
    
    # Verificar ação solicitada
    if action == 'encomendar':
        flash('Funcionalidade de encomenda em desenvolvimento', 'info')
        return redirect(url_for('existencias.existencias'))
    elif action == 'precos':
        flash('Funcionalidade de preços em desenvolvimento', 'info')
        return redirect(url_for('existencias.existencias'))
    
    # Use ExistenciasRepository for product search
    resultados = []
    artigos_sem_stock = []
    
    try:
        # Get enc_forn from session (set during login based on vendor)
        enc_forn = session.get('enc_forn', 'S')
        
        # Use repository to search products
        resultados = existencias_repo.search_products(codigo_artigo, enc_forn)
        
        # If no results with stock, check if products exist without stock
        if not resultados:
            # This would need a new method in the repository, for now use direct query
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT Codigo, Descricao 
                        FROM Artigos 
                        WHERE Codigo STARTING WITH ?
                        ORDER BY Codigo
                    """, (codigo_artigo,))
                    
                    artigos_sem_stock = cursor.fetchall()
                    cursor.close()
                    conn.close()
                except Exception as e:
                    current_app.logger.error(f"Erro ao verificar artigos sem stock: {str(e)}")
                    if conn:
                        conn.close()
            
    except Exception as e:
        flash(f'Erro na consulta: {str(e)}', 'danger')
        current_app.logger.error(f"Erro na consulta de existências: {str(e)}")
    
    return render_template('existencias_resultado.html',
                         resultados=resultados,
                         artigos_sem_stock=artigos_sem_stock,
                         codigo_pesquisa=codigo_artigo,
                         enc_forn=enc_forn)

@existencias_bp.route('/limpar_filtros_existencias')
@login_required
def limpar_filtros_existencias():
    """Limpar os filtros guardados na sessão"""
    # Limpar todos os filtros da sessão
    session.pop('filtro_tipo_artigo', None)
    session.pop('filtro_tipo_ne', None)
    session.pop('filtro_n_cabos', None)
    session.pop('filtro_composicao', None)
    session.pop('filtro_tipo_processo', None)
    session.pop('filtro_enc_forn', None)
    session.pop('filtro_utilizacao', None)
    
    flash('Filtros limpos com sucesso', 'success')
    return redirect(url_for('existencias.existencias'))

@existencias_bp.route('/existencias/detalhes/<codigo>')
@login_required
def existencias_detalhes(codigo):
    """Ver detalhes de existências por lote de um artigo específico"""
    
    resultados_lotes = []
    info_artigo = None
    enc_forn = request.args.get('enc_forn', 'S')
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar informação do artigo
            cursor.execute("""
                SELECT Codigo, Descricao, Unidade, P_Venda1 
                FROM Artigos 
                WHERE Codigo = ?
            """, (codigo,))
            info_artigo = cursor.fetchone()
            
            # Buscar existências por lote
            cursor.execute("""
                SELECT L.Lote, L.Descricao, 
                       E.Stock_Actual, E.Stock_Reservado,
                       E.Stock_Actual - E.Stock_Reservado as Disponivel,
                       L.dt_registo, L.Fornecedor
                FROM Stock_Lotes E
                LEFT JOIN Lotes L ON L.Lote = E.Lote
                WHERE E.Codigo = ?
                AND E.Stock_Actual > 0
                ORDER BY L.dt_registo, L.Lote
            """, (codigo,))
            
            resultados_lotes = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao carregar detalhes: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('existencias_detalhes.html',
                         info_artigo=info_artigo,
                         resultados_lotes=resultados_lotes,
                         enc_forn=enc_forn)

@existencias_bp.route('/api/detalhes_lote/<string:codigo>')
@login_required
def detalhes_lote(codigo):
    """
    API endpoint para buscar detalhes de lote de um artigo.
    Replica a lógica de 'listaexist.php'.
    """
    lotes = []
    conn = get_db_connection()
    
    # DEBUG: Adicionar variáveis de debug
    debug_info = {
        'codigo': codigo,
        'enc_forn': session.get('enc_forn', 'S'),
        'user': session.get('user', 'N/A'),  # Utilizador (U01, U02, etc)
        'vendedor': session.get('vendedor', 'N/A'),  # Vendedor
        'nivel_acesso': session.get('nivel_acesso', 0),
        'sql': None,
        'error': None
    }
    
    if not conn:
        debug_info['error'] = 'Erro de conexão com a base de dados'
        return f"""
        <div class='p-3 text-danger'>
            <h5>ERRO DE CONEXÃO</h5>
            <pre>{debug_info}</pre>
        </div>
        """, 500

    try:
        # Usar um cursor para a query principal e outro para as queries no loop
        main_cursor = conn.cursor()
        lab_cursor = conn.cursor()

        # Use ExistenciasRepository for product details
        enc_forn = session.get('enc_forn', 'S')
        nivel_acesso = session.get('nivel_acesso', 0)
        cd_vend = session.get('cd_vend', session.get('vendedor', ''))
        vendedor = session.get('vendedor', session.get('cd_vend', ''))

        # DEBUG: Show parameters
        print(f"DEBUG - Executando com parâmetros: codigo={codigo}, enc_forn={enc_forn}")
        print(f"DEBUG - Sessão: user={session.get('user')}, vendedor={vendedor}, nivel_acesso={nivel_acesso}")
        
        # Get product details using repository
        lotes_data = existencias_repo.get_product_details(codigo, enc_forn)
        
        debug_info['cd_vend'] = cd_vend
        debug_info['vendedor'] = vendedor
        debug_info['nivel_acesso'] = nivel_acesso
        debug_info['nivel_acesso_sessao'] = session.get('nivel_acesso', 'N/A')

        # Convert to dict format and add lab results - using uppercase keys to match template
        columns = ['RCODIGO', 'RLOTE', 'RLOTEFOR', 'REXIST', 'RSTKDISP', 'RENCCLI', 'RFORNEC', 'RNOMEFOR', 
                  'RDESCRICAO', 'RTIPOSITUA', 'RPVP1', 'RPVP2', 'RPRECO_UN', 'RMOEDA', 'RCOND_ENTREGA', 
                  'RCHAVE', 'RTIPONIVEL', 'RNIVEL', 'RPVP3', 'RPVP4', 'RTIPOSITUADESC', 'RCODIGO_COR',
                  'RARMAZEM', 'RPRECO_COMPRA', 'RSIGLA', 'RFIXACAO', 'RFORMA_PAG_DESC', 'RPRAZO_NDIAS']
        
        for row in lotes_data:
            lote_data = dict(zip(columns, row))
            
            # Get lab results using repository
            lab_results = existencias_repo.get_lab_results(lote_data['RCODIGO'], lote_data['RLOTE'])
            lote_data['LAB_RESULTS'] = lab_results
            
            lotes.append(lote_data)
            
        main_cursor.close()
        lab_cursor.close()
        conn.close()

        # Se não houver lotes, mostrar mensagem de debug
        if not lotes:
            return f"""
            <div class='p-3 text-warning'>
                <h5>Nenhum lote encontrado</h5>
                <details>
                    <summary>Debug Info</summary>
                    <pre>Código: {codigo}
Enc.Fornecedor: {enc_forn}
Utilizador: {session.get('user', 'N/A')}
Vendedor (cd_vend): {vendedor}
Nível: {nivel_acesso}</pre>
                </details>
            </div>
            """

        return render_template('_detalhes_lote_partial.html', 
                             lotes=lotes, 
                             nivel_acesso=nivel_acesso,
                             debug=current_app.debug)  # Add app.debug to template context

    except Exception as e:
        if conn:
            conn.close()
            
        debug_info['error'] = str(e)
        
        # Mostrar informações de debug detalhadas
        return f"""
        <div class='p-3 text-danger'>
            <h5>ERRO AO CONSULTAR DETALHES DO LOTE</h5>
            <details open>
                <summary>Informações de Debug</summary>
                <pre style='background: #f8f9fa; padding: 10px; border-radius: 5px;'>
<b>Código Artigo:</b> {debug_info['codigo']}
<b>Enc.Fornecedor:</b> {debug_info['enc_forn']}
<b>Utilizador:</b> {debug_info.get('user', 'N/A')}
<b>Vendedor (cd_vend):</b> {debug_info.get('vendedor', 'N/A')}
<b>Nível Acesso:</b> {debug_info.get('nivel_acesso', 0)}
<b>Nível na Sessão:</b> {debug_info.get('nivel_acesso_sessao', 'N/A')}

<b>SQL Executado:</b>
{debug_info['sql']}

<b>Erro:</b>
{debug_info['error']}
                </pre>
            </details>
        </div>
        """, 500

@existencias_bp.route('/laboratorio/<codigo>/<lote>')
@login_required
def laboratorio_observacoes(codigo, lote):
    """Página de observações laboratoriais para um artigo/lote específico"""
    
    # Debug logging
    current_app.logger.info(f"Laboratory page requested for codigo={codigo}, lote={lote}")
    
    # Get laboratory data
    lab_data = laboratorio_repo.get_lab_results(codigo, lote)
    
    current_app.logger.info(f"Lab data returned: {lab_data is not None}, type: {type(lab_data)}")
    if lab_data:
        current_app.logger.info(f"Lab data keys: {list(lab_data.keys())}")
        current_app.logger.info(f"Lab data ne_valor: {lab_data.get('ne_valor')}")
    
    return render_template('laboratorio.html',
                         codigo=codigo,
                         lote=lote,
                         lab_data=lab_data)
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import fdb
from decimal import Decimal 
from datetime import datetime, timedelta
from functools import wraps
from config import FIREBIRD_CONFIG, SECRET_KEY
import hashlib

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=8)

# Decorator para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Por favor faça login primeiro', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Conecta ao Firebird"""
    try:
        return fdb.connect(**FIREBIRD_CONFIG)
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return None

@app.route('/')
def index():
    """Redireciona para login ou dashboard"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de login
    - Usuário digita apenas o número (ex: 01, 02, 20, 99)
    - Sistema adiciona prefixo 'U' automaticamente (01 → U01)
    - Compara com campo Utilizador na tabela Utiliza_Web
    - Vendedor é um campo INTEGER na BD
    """
    if request.method == 'POST':
        user_input = request.form.get('user', '').strip()  # Usuário digita só o número
        password = request.form.get('password', '').strip()
        
        if not user_input or not password:
            flash('Por favor preencha todos os campos', 'danger')
            return render_template('login.html')
        
        # Concatenar 'U' ao número digitado
        utilizador_busca = 'U' + user_input  # Ex: 01 vira U01
        
        conn = get_db_connection()
        if not conn:
            flash('Erro ao conectar à base de dados', 'danger')
            return render_template('login.html')
        
        try:
            cursor = conn.cursor()
            
            # Verificar estado da BD
            cursor.execute("SELECT Valor FROM Parametros_GC WHERE Chave = 'BD_ESTADO'")
            estado = cursor.fetchone()
            if estado and estado[0] == 'MANUTENCAO':
                flash('Base de dados em manutenção. Tente mais tarde.', 'warning')
                cursor.close()
                conn.close()
                return render_template('login.html')
            
            # Validar login - Vendedor é INTEGER na BD
            cursor.execute("""
                SELECT Utilizador, Senha, Vendedor 
                FROM Utiliza_Web
                WHERE Utilizador = ? AND Senha = ?
            """, (utilizador_busca, password))
            
            user_data = cursor.fetchone()
            
            if user_data:
                # Login válido - guardar dados na sessão
                session.permanent = True
                session['user'] = user_data[0]      # Utilizador (U01, U02, etc)
                session['vendedor'] = user_data[2]  # Vendedor (INTEGER: 1, 2, 20, 99)
                session['password'] = password       # Password
                session['validar'] = 1
                session['login_time'] = datetime.now().isoformat()
                
                # Determinar nível de acesso baseado no vendedor (INTEGER)
                vendedor = user_data[2]  # Já é um integer
                nivel_acesso = 0
                
                try:
                    # Aplicar lógica do listaexist.php (linha 46-48)
                    if vendedor in [1, 2]:
                        nivel_acesso = 1
                    elif vendedor in [20, 99]:
                        nivel_acesso = 99
                    
                    print(f"DEBUG Login - Vendedor: {vendedor} (tipo: {type(vendedor)}), Nível: {nivel_acesso}")
                    
                except Exception as e:
                    print(f"DEBUG Login - Erro ao calcular nível: {e}")
                    nivel_acesso = 0
                
                session['nivel_acesso'] = nivel_acesso
                
                # Mensagem de boas-vindas
                flash(f'Bem-vindo, Vendedor {vendedor}!', 'success')
                
                print(f"DEBUG Login Sucesso - User: {user_data[0]}, Vendedor: {vendedor}, Nível: {nivel_acesso}")
                
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                flash('Utilizador ou senha inválidos', 'danger')
                print(f"DEBUG Login Falhou - Tentou: {utilizador_busca}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao validar login: {str(e)}', 'danger')
            print(f"DEBUG Login Erro: {str(e)}")
            if conn:
                conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout do utilizador"""
    session.clear()
    flash('Sessão terminada com sucesso', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal com avisos"""
    avisos = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Buscar avisos/lembretes não processados
            cursor.execute("""
                SELECT L.Mensagem, L.Msg_id, L.Remetente, L.recibo_leitura, 
                       U.Descricao, L.Tipo_Msg, L.NPedido, L.Dt_Registo
                FROM Lembretes L
                LEFT OUTER JOIN Utilizadores_GC U ON U.Utilizador = L.Remetente
                WHERE L.destinatario = ? AND L.Processado = 'N'
                ORDER BY L.Dt_Registo DESC
            """, (session['user'],))
            
            avisos = cursor.fetchall()
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao carregar avisos: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('dashboard.html', avisos=avisos)

@app.route('/menu')
@login_required
def menu():
    """Menu principal da aplicação"""
    return render_template('menu.html')

@app.route('/clientes')
@login_required
def clientes():
    """Lista de clientes"""
    clientes_list = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT FIRST 100 Cliente, Nome1, Telefone, Email, Localidade
                FROM Clientes
                WHERE Activo = 'S'
                ORDER BY Nome1
            """)
            clientes_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar clientes: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('clientes.html', clientes=clientes_list)

@app.route('/artigos')
@login_required
def artigos():
    """Lista de artigos"""
    artigos_list = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT FIRST 100 Codigo, Descricao, Unidade, P_Venda1
                FROM Artigos
                WHERE Activo = 'S'
                ORDER BY Descricao
            """)
            artigos_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar artigos: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('artigos.html', artigos=artigos_list)

@app.route('/pedidos')
@login_required
def pedidos():
    """Lista de pedidos"""
    pedidos_list = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT FIRST 50 P.Pedido, P.Cliente, C.Nome1, P.Dt_Registo, 
                       P.Codigo, A.Descricao, P.Quantidade, P.Preco
                FROM Pda_Pedidos P
                LEFT JOIN Clientes C ON C.Cliente = P.Cliente
                LEFT JOIN Artigos A ON A.Codigo = P.Codigo
                WHERE P.Vendedor = ?
                ORDER BY P.Dt_Registo DESC
            """, (session.get('vendedor'),))
            
            pedidos_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar pedidos: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('pedidos.html', pedidos=pedidos_list)

@app.route('/novo_pedido', methods=['GET', 'POST'])
@login_required
def novo_pedido():
    """Criar novo pedido"""
    if request.method == 'POST':
        # Aqui implementaria a lógica para gravar o pedido
        flash('Funcionalidade em desenvolvimento', 'info')
        return redirect(url_for('pedidos'))
    
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

@app.route('/marcar_aviso_lido/<int:msg_id>')
@login_required
def marcar_aviso_lido(msg_id):
    """Marcar aviso como lido"""
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Lembretes 
                SET Processado = 'S', Dt_Processado = CURRENT_TIMESTAMP
                WHERE Msg_id = ? AND destinatario = ?
            """, (msg_id, session['user']))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Aviso marcado como lido', 'success')
        except Exception as e:
            flash(f'Erro ao marcar aviso: {str(e)}', 'danger')
            if conn:
                conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/estatisticas')
@login_required
def estatisticas():
    """Página de estatísticas e relatórios"""
    stats = {}
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Usar vendedor (INTEGER) para as queries
            vendedor = session.get('vendedor', 0)
            
            # Total de pedidos do vendedor
            cursor.execute("""
                SELECT COUNT(*), SUM(Quantidade * Preco)
                FROM Pda_Pedidos
                WHERE Vendedor = ?
            """, (vendedor,))
            result = cursor.fetchone()
            stats['total_pedidos'] = result[0] or 0
            stats['valor_total'] = result[1] or 0
            
            # Pedidos do mês
            cursor.execute("""
                SELECT COUNT(*), SUM(Quantidade * Preco)
                FROM Pda_Pedidos
                WHERE Vendedor = ? 
                AND EXTRACT(MONTH FROM Dt_Registo) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM Dt_Registo) = EXTRACT(YEAR FROM CURRENT_DATE)
            """, (vendedor,))
            result = cursor.fetchone()
            stats['pedidos_mes'] = result[0] or 0
            stats['valor_mes'] = result[1] or 0
            
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar estatísticas: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('estatisticas.html', stats=stats)

@app.route('/api/search_cliente')
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

@app.route('/existencias')
@login_required
def existencias():
    """Página de consulta de existências/stock"""
    
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
                         tipo_processo=tipo_processo)

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

@app.route('/existencias_consulta', methods=['POST'])
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
    
    # Formar código do artigo
    codigo_artigo = formar_codigo_artigo(tipo_art, tipo_ne, n_cabos, composicao, tipo_processo, utilizacao)
    
    # Guardar na sessão para uso posterior
    session['ultimo_codigo_pesquisa'] = codigo_artigo
    session['enc_forn'] = enc_forn
    session['tipo_processo'] = tipo_processo
    
    # Verificar ação solicitada
    if action == 'encomendar':
        flash('Funcionalidade de encomenda em desenvolvimento', 'info')
        return redirect(url_for('existencias'))
    elif action == 'precos':
        flash('Funcionalidade de preços em desenvolvimento', 'info')
        return redirect(url_for('existencias'))
    
    # Para consultar, buscar resultados
    resultados = []
    artigos_sem_stock = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Chamar stored procedure Inq_Exist_Lote_Pda
            # Nota: Ajustar parâmetros conforme necessário
            sql = """
                SELECT RDescricao, RCodigo, RCodigoSubstituto, 
                       SUM(RExist) as TotalExist,
                       SUM(REncCli) as TotalEncCli,
                       SUM(RExist - REncCli) as Disponivel
                FROM Inq_Exist_Lote_Pda(?, ?, 3, 4, 'TUDO', 0, '31.12.3000', 'S', '31.12.3000', 0, 'S', 1, 2, 2)
                WHERE RCodigo STARTING WITH ?
                GROUP BY RDescricao, RCodigo, RCodigoSubstituto
                ORDER BY RCodigo ASC
            """
            
            codigo_fim = codigo_artigo + 'z'
            cursor.execute(sql, (codigo_artigo, codigo_fim, codigo_artigo))
            
            resultados = cursor.fetchall()
            
            # Se não houver resultados com stock, verificar se artigos existem
            if not resultados:
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
            flash(f'Erro na consulta: {str(e)}', 'danger')
            if conn:
                conn.close()
    
    return render_template('existencias_resultado.html',
                         resultados=resultados,
                         artigos_sem_stock=artigos_sem_stock,
                         codigo_pesquisa=codigo_artigo,
                         enc_forn=enc_forn)

@app.route('/existencias_detalhes/<codigo>')
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
                       L.Data_Validade, L.Fornecedor
                FROM Stock_Lotes E
                LEFT JOIN Lotes L ON L.Lote = E.Lote
                WHERE E.Codigo = ?
                AND E.Stock_Actual > 0
                ORDER BY L.Data_Validade, L.Lote
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

def get_lab_results(cursor, codigo, lote):
    """Função auxiliar para buscar resultados de laboratório, como em listaexist.php."""
    try:
        sql_lab = """
            SELECT FIRST 1 
                   L.Ne_Valor, L.Ne_Cv, L.Uster_CVM, L.Uster_PNTFinos2, L.Uster_PNTGrossos2, 
                   L.Uster_Neps_2, L.Rkm_Valor, L.Rkm_Cv, L.Rkm_Along_Valor, L.Rkm_Along_Cv, 
                   L.Tipo_Torcao, L.Torcao_TPI_Valor, L.Tipo_Torcao_S, L.Torcao_TPI_Valor_S, 
                   T.Nr_Fios, L.Uster_Pilosidade, L.Uster_Pilosidade_Cv, L.Uster_Neps_3, 
                   L.Tipo_Processo
            FROM Ficha_Lab_Lote L 
            LEFT OUTER JOIN Tipo_Torcedura T ON T.Tipo = L.Tipo_Torcedura 
            WHERE L.Codigo = ? AND L.Lote = ? 
            ORDER BY L.nr_relatorio DESC
        """
        cursor.execute(sql_lab, (codigo, lote))
        row = cursor.fetchone()
        if row:
            # Índices baseados na query PHP
            Uster_PNTFinos = row[3] if row[3] else ''
            Uster_PNTGrossos = row[4] if row[4] else ''
            Uster_Neps2 = row[5] if row[5] else ''
            Uster_Neps3 = row[17] if row[17] else ''
            Rkm_Valor = row[6] if row[6] else ''
            Tipo_Processo = row[18] if row[18] else ''

            if Tipo_Processo == 'O':
                return f"<b>PF:</b>{Uster_PNTFinos} <b>PG:</b>{Uster_PNTGrossos} <b>NP:</b>{Uster_Neps3} <b>RK:</b>{Rkm_Valor}"
            else:
                return f"<b>PF:</b>{Uster_PNTFinos} <b>PG:</b>{Uster_PNTGrossos} <b>NP:</b>{Uster_Neps2} <b>RK:</b>{Rkm_Valor}"
    except Exception as e:
        print(f"Erro ao buscar dados de lab para {codigo}/{lote}: {e}")
    return "N/A"

@app.route('/api/detalhes_lote/<string:codigo>')
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

        # Query exata do listaexist.php (linha 62-66)
        sql = """
            SELECT RCodigo, RLote, RLoteFor, RExist, (RExist - REncCli + REncFor) as RStkDisp,
                   REncCli, RFornec, RNomeFor, RDescricao, RTipoSitua, RPvp1, RPvp2, RPreco_UN, RMoeda,
                   RCond_Entrega, RChave, RTipoNivel, RNivel, RPvp3, RPvp4, RTipoSituaDesc, RCodigo_Cor,
                   RArmazem, RPreco_Compra, RSigla, RFixacao, RForma_Pag_Desc, RPrazo_NDias
            FROM Inq_Exist_Lote_Pda_2(?, ?, 3, 4, 'ACT', 0, '31.12.3000', ?, '31.12.3000', 0, 'S', 1, 2, 2)
            ORDER BY RChave ASC, RExist ASC, ROrdem
        """
        
        debug_info['sql'] = sql
        enc_forn = session.get('enc_forn', 'S')
        
        # Usar o nível de acesso já calculado no login
        nivel_acesso = session.get('nivel_acesso', 0)
        cd_vend = session.get('cd_vend', session.get('vendedor', ''))
        vendedor = session.get('vendedor', session.get('cd_vend', ''))

        # DEBUG: Mostrar parâmetros
        print(f"DEBUG - Executando SQL com parâmetros: codigo={codigo}, enc_forn={enc_forn}")
        print(f"DEBUG - Sessão: user={session.get('user')}, vendedor={session.get('vendedor')}, nivel_acesso={session.get('nivel_acesso')}")
        
        main_cursor.execute(sql, (codigo, codigo, enc_forn))
        
            
        # DEBUG: Adicionar informação de sessão
        debug_info['cd_vend'] = cd_vend
        debug_info['vendedor'] = vendedor
        debug_info['nivel_acesso'] = nivel_acesso
        debug_info['nivel_acesso_sessao'] = session.get('nivel_acesso', 'N/A')

        for row in main_cursor.fetchall():
            lote_data = dict(zip([desc[0] for desc in main_cursor.description], row))
            
            # Buscar resultados do laboratório (como no PHP)
            lote_data['LAB_RESULTS'] = get_lab_results(lab_cursor, lote_data['RCODIGO'], lote_data['RLOTE'])
            
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
                             debug=app.debug)  # Add app.debug to template context

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
            
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
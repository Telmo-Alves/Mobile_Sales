"""
Dashboard and menu routes for Mobile Sales application
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..utils import login_required
from ..database.connection import get_db_connection
from ..database import clientes_repo

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
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

@dashboard_bp.route('/menu')
@login_required
def menu():
    """Menu principal da aplicação"""
    return render_template('menu.html')

@dashboard_bp.route('/clientes')
@login_required
def clientes():
    """Lista de clientes"""
    clientes_list = []
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT FIRST 100 l.Cliente, l.Nome1, l.Telefone1, l.Email, l.Zona
                FROM Locais_Entrega l
                INNER JOIN Clientes c ON c.Cliente = l.Cliente
                WHERE c.Situacao IN ('ACT', 'MANUT')
                AND l.Local_ID = 'SEDE'
                ORDER BY l.Nome1
            """)
            clientes_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Erro ao carregar clientes: {str(e)}', 'warning')
            if conn:
                conn.close()
    
    return render_template('clientes.html', clientes=clientes_list)

@dashboard_bp.route('/artigos')
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

@dashboard_bp.route('/marcar_aviso_lido/<int:msg_id>')
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
    
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/estatisticas')
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

@dashboard_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    """Página de configurações do sistema - só para nivel_acesso >= 2"""
    if session.get('nivel_acesso', 0) < 2:
        flash('Acesso negado. Apenas administradores podem alterar configurações.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    # Import config here to avoid circular imports
    from config import FIREBIRD_CONFIG, WAREHOUSE_CONFIG
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Obter dados do formulário
        config_data = {
            'host': request.form.get('host', '').strip(),
            'port': int(request.form.get('port', 3050)),
            'database': request.form.get('database', '').strip(),
            'user': request.form.get('user', '').strip(),
            'password': request.form.get('password', '').strip(),
            'charset': request.form.get('charset', 'WIN1252').strip()
        }
        
        # Obter dados dos armazéns
        warehouse_data = {
            'arm_ini': int(request.form.get('arm_ini', 1)),
            'arm_fim': int(request.form.get('arm_fim', 999))
        }
        
        if action == 'test':
            # Testar ligação
            try:
                import fdb
                conn = fdb.connect(
                    host=config_data['host'],
                    port=config_data['port'],
                    database=config_data['database'],
                    user=config_data['user'],
                    password=config_data['password'],
                    charset=config_data['charset']
                )
                cursor = conn.cursor()
                cursor.execute("SELECT FIRST 1 * FROM RDB$DATABASE")
                cursor.fetchone()
                cursor.close()
                conn.close()
                
                from flask import jsonify
                return jsonify({
                    'success': True,
                    'message': f'Ligação bem-sucedida!\n\nServidor: {config_data["host"]}:{config_data["port"]}\nBase de Dados: {config_data["database"]}\nUtilizador: {config_data["user"]}'
                })
            except Exception as e:
                from flask import jsonify
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        elif action == 'save':
            # Validar dados
            required_fields = ['host', 'database', 'user', 'password']
            for field in required_fields:
                if not config_data[field]:
                    flash(f'Campo "{field}" é obrigatório.', 'error')
                    return render_template('configuracoes.html', config=FIREBIRD_CONFIG)
            
            try:
                # Testar ligação antes de guardar
                import fdb
                conn = fdb.connect(
                    host=config_data['host'],
                    port=config_data['port'],
                    database=config_data['database'],
                    user=config_data['user'],
                    password=config_data['password'],
                    charset=config_data['charset']
                )
                cursor = conn.cursor()
                cursor.execute("SELECT FIRST 1 * FROM RDB$DATABASE")
                cursor.fetchone()
                cursor.close()
                conn.close()
                
                # Criar backup do config atual
                import shutil
                from datetime import datetime
                backup_name = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                
                try:
                    shutil.copy('/var/www/html/Mobile_Sales/config.py', f'/var/www/html/Mobile_Sales/{backup_name}')
                except PermissionError:
                    # Se não conseguir criar backup no diretório principal, usar /tmp
                    backup_name = f"/tmp/{backup_name}"
                    shutil.copy('/var/www/html/Mobile_Sales/config.py', backup_name)
                    print(f"Backup criado em /tmp devido a permissões: {backup_name}")
                except Exception as e:
                    print(f"Erro ao criar backup: {str(e)}")
                    # Continuar mesmo sem backup
                
                # Escrever novo config.py
                config_content = f"""# Configuração do Firebird para fdb
FIREBIRD_CONFIG = {{
    'host': '{config_data['host']}',
    'port': {config_data['port']},
    'database': '{config_data['database']}',
    'user': '{config_data['user']}',
    'password': '{config_data['password']}',
    'charset': '{config_data['charset']}'
}}

# Configuração dos Armazéns
WAREHOUSE_CONFIG = {{
    'arm_ini': {warehouse_data['arm_ini']},    # Armazém inicial
    'arm_fim': {warehouse_data['arm_fim']}   # Armazém final
}}

# Configuração Flask
SECRET_KEY = 'chave-flask-mobile-sales'
DEBUG = True
"""
                
                with open('/var/www/html/Mobile_Sales/config.py', 'w', encoding='utf-8') as f:
                    f.write(config_content)
                
                flash(f'Configurações guardadas com sucesso! Backup criado: {backup_name}', 'success')
                print(f"Configurações alteradas por {session.get('user')} - Backup: {backup_name}")
                
                # Reiniciar Apache para aplicar alterações
                import subprocess
                try:
                    # Como root, não precisamos de sudo
                    subprocess.run(['systemctl', 'restart', 'apache2.service'], check=True, capture_output=True)
                    flash('Sistema reiniciado para aplicar alterações.', 'success')
                except subprocess.CalledProcessError as e:
                    flash(f'Aviso: Erro ao reiniciar sistema automaticamente: {e}', 'warning')
                except FileNotFoundError:
                    # Se systemctl não for encontrado, tentar service
                    try:
                        subprocess.run(['service', 'apache2', 'restart'], check=True, capture_output=True)
                        flash('Sistema reiniciado para aplicar alterações.', 'success')
                    except Exception as e2:
                        flash(f'Aviso: Não foi possível reiniciar automaticamente. Reinicie manualmente: {e2}', 'warning')
                
            except Exception as e:
                flash(f'Erro ao testar/guardar configurações: {str(e)}', 'error')
                print(f"Erro nas configurações: {str(e)}")
    
    return render_template('configuracoes.html', config=FIREBIRD_CONFIG, warehouse_config=WAREHOUSE_CONFIG)

@dashboard_bp.route('/mapabordocli')
@login_required
def mapabordocli():
    """Mapa de Bordo de Clientes - Form para seleção de cliente"""
    vendedor = session.get('vendedor', 0)
    clientes_list = clientes_repo.get_clients_for_vendor(vendedor)
    return render_template('mapabordocli.html', clientes=clientes_list)

@dashboard_bp.route('/listamapabordocli', methods=['POST'])
@login_required
def listamapabordocli():
    """Mapa de Bordo de Clientes - Exibir dados do cliente selecionado"""
    cliente_id = request.form.get('cliente')
    vendedor = session.get('vendedor', 0)
    
    if not cliente_id:
        flash('Selecione um cliente', 'error')
        return redirect(url_for('dashboard.mapabordocli'))
    
    # Get customer dashboard data
    dashboard_data = clientes_repo.get_customer_dashboard_data(cliente_id, vendedor)
    
    if not dashboard_data:
        flash('Não foi possível obter dados do cliente', 'error')
        return redirect(url_for('dashboard.mapabordocli'))
    
    # Store in session for potential detail views
    session['cliente'] = cliente_id
    session['nome_cli'] = dashboard_data['nome']
    
    return render_template('listamapabordocli.html', 
                         data=dashboard_data,
                         vendedor=vendedor)
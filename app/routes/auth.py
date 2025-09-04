"""
Authentication routes for Mobile Sales application
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import timedelta, datetime
from ..utils import login_required
from ..database import auth_repo
from ..database.connection import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Redireciona para login ou menu"""
    if 'user' in session:
        return redirect(url_for('dashboard.menu'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
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
            
            # Use AuthRepository for authentication
            try:
                user_data = auth_repo.authenticate_user(utilizador_busca, password)
                
                if user_data:
                    # Login successful - save session data
                    session.permanent = True
                    session['user'] = utilizador_busca
                    session['vendedor'] = user_data['vendedor']
                    session['password'] = password
                    session['validar'] = 1
                    session['login_time'] = datetime.now().isoformat()
                    session['nivel_acesso'] = user_data['nivel_acesso']
                    
                    vendedor = user_data['vendedor']
                    nivel_acesso = user_data['nivel_acesso']
                    
                    print(f"DEBUG Login - Vendedor: {vendedor} (tipo: {type(vendedor)}), Nível: {nivel_acesso}")
                    
                    # Welcome message
                    flash(f'Bem-vindo, Vendedor {vendedor}!', 'success')
                    
                    print(f"DEBUG Login Sucesso - User: {utilizador_busca}, Vendedor: {vendedor}, Nível: {nivel_acesso}")
                    
                    cursor.close()
                    conn.close()
                    
                    # Check if there's a next_url to redirect to
                    next_url = session.pop('next_url', None)
                    if next_url:
                        return redirect(next_url)
                    return redirect(url_for('dashboard.menu'))
                else:
                    flash('Utilizador ou senha inválidos', 'danger')
                    print(f"DEBUG Login Falhou - Tentou: {utilizador_busca}")
                    
            except Exception as e:
                flash('Erro interno na autenticação. Tente novamente.', 'error')
                print(f"DEBUG Login Erro: {str(e)}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Erro ao validar login: {str(e)}', 'danger')
            print(f"DEBUG Login Erro: {str(e)}")
            if conn:
                conn.close()
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Logout do utilizador"""
    session.clear()
    flash('Sessão terminada com sucesso', 'info')
    return redirect(url_for('auth.login'))
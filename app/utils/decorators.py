"""
Decorators for Flask routes
"""

from functools import wraps
from flask import session, redirect, url_for, request, flash

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'validar' not in session or session.get('validar') != 1:
            # Store intended destination
            session['next_url'] = request.url
            flash('Por favor, faça login para aceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
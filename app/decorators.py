from functools import wraps
from flask import session, flash, redirect, url_for

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("You do not have permission to access this page", "danger")
            return redirect(url_for('api.login'))
        return f(*args, **kwargs)
    return decorated_function

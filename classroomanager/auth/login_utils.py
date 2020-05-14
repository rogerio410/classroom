from functools import wraps
from flask import g, request, redirect, url_for, session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_loggedin():
            session['next'] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


def is_loggedin():
    return 'credentials' in session

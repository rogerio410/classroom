from flask import render_template
from classroomanager import app
from classroomanager.auth.login_utils import login_required


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.errorhandler(404)
def not_found(e):
    return 'Sumiu.... (lost...)'

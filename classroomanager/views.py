from flask import render_template
from classroomanager import app
from classroomanager.auth.login_utils import login_required


@app.route('/')
@login_required
def index():
    return render_template('index.html')

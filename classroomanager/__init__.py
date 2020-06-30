# https: // flask.palletsprojects.com/en/1.1.x/patterns/packages/
# https://flask.palletsprojects.com/en/1.1.x/blueprints/#

import os
from flask import Flask
from classroomanager.auth.views import auth
from classroomanager.core.views import core

app = Flask(__name__)

app.secret_key = 'AS<MNAS$##$#)---'

# To run:
# export FLASK_APP=classroomanager
# export FLASK_ENV=development
# flask run


def setup():

    # Register module (blueprints)
    app.register_blueprint(auth)
    app.register_blueprint(core)

    # import view out a blueprint
    import classroomanager.views

    #  When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


setup()

# Ahttps: // flask.palletsprojects.com/en/1.1.x/patterns/packages/

import os
from flask import Flask
app = Flask(__name__)

app.secret_key = 'AS<MNAS$##$#)---'


def setup():

    # Save by 'Save without Formating'
    import classroomanager.controllers
    import classroomanager.google_oauth_controllers

    #  When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


setup()

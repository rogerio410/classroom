# https: // flask.palletsprojects.com/en/1.1.x/patterns/packages/


from flask import Flask
app = Flask(__name__)

app.secret_key = 'HELLO-BATMAN...'

# Save by 'Save without Formating'
import classroomanager.controllers

# https://developers.google.com/identity/protocols/oauth2/web-server
import flask
import requests
import simplejson
from classroomanager import app
from .classroom_operacoes import *
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient

CLIENT_SECRETS_FILE = 'credentials_webserver.json'
# https://developers.google.com/identity/protocols/oauth2/scopes
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile']

API_SERVICE_NAME = 'classroom'
API_VERSION = 'v1'


@app.route('/test')
def test_api_request():

    print('Rogerio da Silva')
    if 'credentials' not in flask.session:
        flask.session['next'] = '/test'
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    classroom = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    disciplinas = obter_disciplinas(classroom)

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.jsonify(disciplinas)


@app.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)
    flask.session['profile'] = _request_user_info(credentials)
    next = flask.session.get('next') or '/test'
    return flask.redirect(next)


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return flask.redirect('/')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return 'Credentials successfully revoked.'
    else:
        return 'An error occurred.'


@app.route('/logout')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return flask.redirect('/')


def _request_user_info(credentials):
    response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo',
                            headers={'Authorization': 'Bearer ' + credentials.token},)

    if response.status_code == 200:
        return simplejson.loads(response.content.decode('utf-8'))


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

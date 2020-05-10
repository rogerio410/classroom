from __future__ import print_function
from enum import Enum
import pickle
import os.path
import flask
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient

# obter OAuth Configuration from... tipo: Desktop App
# https://developers.google.com/classroom/guides/auth
# Baixar credentials.json e colar na pasta raiz.., apagar token.pickle


# If modifying these scopes, delete the file token.pickle.
# https://developers.google.com/resources/api-libraries/documentation/classroom/v1/cpp/latest/classgoogle__classroom__api_1_1ClassroomService_1_1SCOPES.html

# SCOPES = ['https://www.googleapis.com/auth/classroom.courses',
#           'https://www.googleapis.com/auth/classroom.coursework.students',
#           'https://www.googleapis.com/auth/classroom.rosters',
#           'https://www.googleapis.com/auth/classroom.profile.emails',
#           'https://www.googleapis.com/auth/classroom.profile.photos'
#           ]

SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile']

API_SERVICE_NAME = 'classroom'
API_VERSION = 'v1'


def get_classroom_service():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    classroom = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    return classroom


def get_classroom_service_from_json():
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('classroom', 'v1', credentials=creds)

    return service


class StatusTurma(Enum):
    ACTIVE = 'ACTIVE'
    ARCHIVED = 'ARCHIVED'
    PROVISIONED = 'PROVISIONED'

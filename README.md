## Classroom Manager

# Gerenciador para Google Classroom

### Prepare Google Project
* Create a Project on Google Cloud
* Enable Classroom API 
* Generate authorization credentials for the project
* Save credentials json as 'credentials_webserver.json' on root folder

[Step-by-step](https://developers.google.com/identity/protocols/oauth2/web-server#example)



# on terminal:
```
$ pip install -r requirements.txt
$ export FLASK_APP=classroomanager
$ export FLASK_ENV=development
$ flask run
```
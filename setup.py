from setuptools import setup


setup(
    name='classroomanager',
    packages=['classroomanager', ]
    include_package_date=True
)

# https://flask.palletsprojects.com/en/1.1.x/patterns/packages/
# on terminal:
# export FLASK_APP=classroomanager
# export FLASK_ENV=development
# flask run

# with gunicorn:
# gunicorn classroomanager:app

# to deploy on heroku
# checkout to deploy
# Merge from master to deploy
# un-ignore crendentials.webserver.json
# git push heroku deploy:master
# this process save sensitive files only in deploy

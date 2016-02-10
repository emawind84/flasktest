import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir, app_root

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = app_root + '/login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from app import views, models

app.register_blueprint(views.bp, url_prefix = app_root)
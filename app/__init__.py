import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_openid import OpenID
from config import basedir, app_root
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = app_root + '/login'
lm.refresh_view = app_root + '/login'
lm.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
lm.needs_refresh_message_category = "info"
oid = OpenID(app, os.path.join(basedir, 'tmp'))

es = Elasticsearch()

import app_logging

from app import views, models

app.register_blueprint(views.bp, url_prefix = app_root)
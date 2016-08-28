import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'this is an hard secret key'

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}]

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

#SERVER_NAME = ''

app_root = '/microblog'

# mail server settings
MAIL_SERVER = 'srv56.hosting24.com'
MAIL_PORT = 587
MAIL_USERNAME = 'emanuele.disco@emawind.com'
MAIL_PASSWORD = 'fHre5sdhyJg1'
MAIL_SECURED = True

# administrator list
ADMINS = ['emanuele.disco@emawind.com']

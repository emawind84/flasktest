#!flask/bin/python

from flask_mail import Message
from app import app, mail
from config import ADMINS

msg = Message("testing sending message", sender=ADMINS[0], recipients=ADMINS)
msg.html = "<p>Ciao</p>"

with app.app_context():
    mail.send(msg)
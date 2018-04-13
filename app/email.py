from flask import render_template
from flask_mail import Message
from app import app, mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body, sender = app.config['ADMINS'][0]):
    msg = Message(subject, sender=sender, recipients=recipients) # recipients as a list
    msg.body = text_body
    msg.html = html_body
    # mail.send(msg)
    Thread(target=send_async_email, args=(app, msg)).start() # .end() ?

def send_password_reset_email(user):
    token = user.get_reset_password_token() # expires_in=600 by default
    send_email('[RohanApp] Reset Your Password',
               # sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token))
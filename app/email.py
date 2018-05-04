from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body, attachments=None, sync=False):
    # attachments is list of triples
    msg = Message(subject, sender=sender, recipients=recipients) # recipients as a list
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else: # corresponds to latter 'if'
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start() # .end() ?
        # ._get_current_object() ?
from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap # This is responsive !!
from flask_moment import Moment
from flask_babel import Babel
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler # StreamHandler
import os
from elasticsearch import Elasticsearch
from redis import Redis
import rq
# from rq import Worker, Queue, Connection
# import os
# from urllib.parse import urlparse

def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None # None during unit testing
    # print('THE REDIS_URL CONFIG VAR IS: ' + app.config['REDIS_URL'])
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    # listen = ['high', 'default', 'low']
    # REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    # app.conn = Redis.from_url(REDIS_URL)

    # urlparse.uses_netloc.append('redis')
    # url = urlparse(REDIS_URL)
    # app.conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)
    app.task_queue = rq.Queue('rohanapp-tasks', connection=app.redis)

    # if __name__ == '__main__':
    #    with Connection(app.conn):
    #        worker = Worker(map(Queue, listen))
    #        worker.work()

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp) # why no URL prefix ?

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') # e.g., http://localhost:5000/auth/login

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'],
                subject='RohanApp Failure', # ideally only 500 errors
                credentials=auth,
                secure=secure)
            mail_handler.setLevel(logging.ERROR) # only errors, not warnings
            app.logger.addHandler(mail_handler)
    
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/rohanapp.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO) # records each instance of the app starting up
        app.logger.info('RohanApp startup')

    return app

from app import models # models is common to all blueprints

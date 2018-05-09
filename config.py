import os
from dotenv import load_dotenv # Do not add .env file to version control !!! ***

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 10
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    REDIS_URL = 'redis://h:p23ccaf9db749cf631b6b462553407ae0e99286e3dbb9fec28283b60b88730ff5@ec2-52-55-90-143.compute-1.amazonaws.com:45769'
    # os.environ.get('REDISTOGO_URL') or 'redis://' # REDIS_URL
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25) # is int() really necessary here?
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None # TLS = Transport Layer Security
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['rohanapp.email@gmail.com']

# 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
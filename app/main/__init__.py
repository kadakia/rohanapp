from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes # just view functions, so not importing forms
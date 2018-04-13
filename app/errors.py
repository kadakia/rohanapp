from flask import render_template
from app import app, db

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404 # default value after the comma is 200

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback() # don't fully understand why this is necessary
    return render_template('500.html'), 500
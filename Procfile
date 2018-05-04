web: flask db upgrade; flask translate compile; gunicorn rohanapp:app
worker: rq worker rohanapp-tasks

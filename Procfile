web: flask db upgrade; flask translate compile; gunicorn rohanapp:app
worker: rq worker -u $REDIS_URL rohanapp-tasks

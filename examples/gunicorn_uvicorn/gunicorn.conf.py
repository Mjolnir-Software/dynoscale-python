import os
# noinspection PyUnresolvedReferences
import log_config

# ENV vars
PORT = int(os.getenv('PORT', '3000'))
WEB_CONCURRENCY = int(os.getenv('WEB_CONCURRENCY', '10'))

# Gunicorn config

wsgi_app = "web:app"
# worker_class = 'uvicorn.workers.UvicornWorker'
worker_class = 'dynoscale.uvicorn.DynoscaleUvicornWorker'

bind = f"0.0.0.0:{PORT}"
preload_app = True

workers = WEB_CONCURRENCY
max_requests = 1000
max_requests_jitter = 25

accesslog = '-'
loglevel = 'debug'

import os

from dynoscale.hooks.gunicorn import pre_request as hook  # noqa # pylint: disable=unused-import

PORT = int(os.getenv('PORT', '3000'))
WORKERS = int(os.getenv('WEB_CONCURRENCY', '3'))
bind = f"0.0.0.0:{PORT}"
max_requests = 10
max_requests_jitter = 3
workers = WORKERS
wsgi_app = "examples.flask_simple.flask_simple:app"


def pre_request(worker, req):
    hook(worker, req)
    # ...do your own thing...

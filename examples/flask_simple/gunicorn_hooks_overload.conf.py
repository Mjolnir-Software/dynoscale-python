from dynoscale.hooks.gunicorn import pre_request as hook  # noqa # pylint: disable=unused-import

bind = "127.0.0.1:3000"
max_requests = 10
max_requests_jitter = 3
workers = 3
wsgi_app = "examples.flask_simple.flask_simple:app"


def pre_request(worker, req):
    hook(worker, req)
    # ...do your own thing...

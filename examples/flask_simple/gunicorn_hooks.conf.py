from dynoscale.hooks.gunicorn import pre_request  # noqa # pylint: disable=unused-import

bind = "127.0.0.1:3000"
max_requests = 10
max_requests_jitter = 3
workers = 3
wsgi_app = "flask_simple:app"
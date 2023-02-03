import os

# from dynoscale.hooks.gunicorn import pre_request  # noqa # pylint: disable=unused-import

PORT = int(os.getenv('PORT', '3000'))
WORKERS = int(os.getenv('WEB_CONCURRENCY', '3'))
bind = f"0.0.0.0:{PORT}"
max_requests = 10
max_requests_jitter = 2
workers = WORKERS
preload_app = True
worker_class = 'uvicorn.workers.UvicornWorker'
wsgi_app = "web:app"  # Yes, this is ASGI app...


def on_starting(server):
    print(f"---------------------------------------------------      HOOK: on_starting {server}")


def on_reload(server):
    print(f"---------------------------------------------------      HOOK: on_reload {server}")


def when_ready(server):
    print(f"---------------------------------------------------      HOOK: when_ready {server}")


def pre_fork(server, worker):
    print(f"---------------------------------------------------      HOOK: pre_fork {server}, {worker}")


def post_fork(server, worker):
    print(f"---------------------------------------------------      HOOK: post_fork {server}, {worker}")


def post_worker_init(worker):
    print(f"---------------------------------------------------      HOOK: post_worker_init {worker}")


def worker_int(worker):
    print(f"---------------------------------------------------      HOOK: worker_int {worker}")


def worker_abort(worker):
    print(f"---------------------------------------------------      HOOK: worker_abort {worker}")


def pre_exec(server):
    print(f"---------------------------------------------------      HOOK: pre_exec {server}")


def pre_request(worker, req):
    print(f"---------------------------------------------------      HOOK: pre_request {worker}, {req}")


def post_request(worker, req, environ, resp):
    print(
        f"---------------------------------------------------      HOOK: post_request {worker}, {req}, {environ}, {resp}"
    )


def child_exit(server, worker):
    print(f"---------------------------------------------------      HOOK: child_exit {server}, {worker}")


def worker_exit(server, worker):
    print(f"---------------------------------------------------      HOOK: worker_exit {server}, {worker}")


def nworkers_changed(server, new_value, old_value):
    print(
        f"---------------------------------------------------      HOOK: nworkers_changed {server}, {new_value}, {old_value}"
    )


def on_exit(server):
    print(f"---------------------------------------------------      HOOK: on_exit {server}")

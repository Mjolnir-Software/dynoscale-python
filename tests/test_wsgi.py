import logging

import pytest

logging.basicConfig(level=logging.DEBUG)

__clbl = lambda a, b: "c"


@pytest.fixture
def app():
    return __clbl


@pytest.fixture
def environ():
    return {"HTTP_X_REQUEST_START": "1234123434"}


@pytest.fixture
def start_response():
    from types import SimpleNamespace
    ns = SimpleNamespace()
    ns.__call__ = lambda _: None
    return ns


def test_dynoscale_wsgi_app_doesnt_crash_with_invalid_settings(env_invalid, app):
    from dynoscale.wsgi import DynoscaleWsgiApp
    DynoscaleWsgiApp(app)


def test_dynoscale_wsgi_app_doesnt_crash_with_valid_settings(env_valid, app):
    from dynoscale.wsgi import DynoscaleWsgiApp
    DynoscaleWsgiApp(app)


def test_dynoscale_wsgi_app_call_doesnt_crash_with_invalid_settings(env_invalid, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    dwa = DynoscaleWsgiApp(app)
    dwa(environ, start_response)


def test_dynoscale_wsgi_app_call_doesnt_crash_with_valid_settings(env_valid, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    dwa = DynoscaleWsgiApp(app)
    dwa(environ, start_response)


def test_dynoscale_wsgi_app_pre_request_doesnt_crash_with_invalid_settings(env_valid, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    dwa = DynoscaleWsgiApp(app)
    dwa(environ, start_response)
    dwa.log_queue_time(environ)


def test_dynoscale_wsgi_app_pre_request_doesnt_crash_with_valid_settings(env_invalid, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    dwa = DynoscaleWsgiApp(app)
    dwa(environ, start_response)
    dwa.log_queue_time(environ)

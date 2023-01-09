import logging

import pytest

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def app():
    def app_callable(a, b):
        return "c"

    return app_callable


@pytest.fixture
def environ():
    return {"HTTP_X_REQUEST_START": "1234123434"}


@pytest.fixture
def start_response():
    from types import SimpleNamespace
    ns = SimpleNamespace()
    ns.__call__ = lambda _: None
    return ns


def test_dynoscale_wsgi_app_init_doesnt_crash_with_valid_settings(env_valid, app):
    from dynoscale.wsgi import DynoscaleWsgiApp
    DynoscaleWsgiApp(app)


def test_dynoscale_wsgi_app_init_doesnt_crash_with_invalid_settings(env_invalid_missing_dyno, app):
    from dynoscale.wsgi import DynoscaleWsgiApp
    DynoscaleWsgiApp(app)


def test_dynoscale_wsgi_app_call_doesnt_crash_with_valid_settings(env_valid, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    dwa = DynoscaleWsgiApp(app)
    dwa(environ, start_response)


def test_dynoscale_wsgi_app_call_doesnt_crash_with_invalid_settings(
        env_invalid_missing_dyno, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    dwa = DynoscaleWsgiApp(app)
    dwa(environ, start_response)


def test_dynoscale_wsgi_app_call_doesnt_crash_ever(env_invalid_missing_dyno, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    dwa = DynoscaleWsgiApp(app)
    dwa.config = None
    dwa(environ, start_response)


def test_dynoscale_wsgi_app_log_queue_time_doesnt_crash_with_valid_settings(
        env_invalid_missing_dyno, app, environ, start_response):
    from dynoscale.wsgi import DynoscaleWsgiApp
    ds_app = DynoscaleWsgiApp(app)
    ds_app(environ, start_response)
    ds_app.log_queue_time(environ)


def test_dynoscale_wsgi_app_log_queue_time_doesnt_crash_with_invalid_settings(
        env_valid,
        app,
        environ,
        start_response,
        caplog
):
    from dynoscale.wsgi import DynoscaleWsgiApp
    ds_app = DynoscaleWsgiApp(app)
    ds_app(environ, start_response)
    with caplog.at_level('INFO'):
        caplog.clear()
        ds_app.log_queue_time({})
        assert caplog.record_tuples
        assert len(caplog.record_tuples) == 1
        assert caplog.record_tuples == [('dynoscale.wsgi.DynoscaleWsgiApp', 20, 'Can not calculate queue time.')]

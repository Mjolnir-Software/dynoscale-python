import logging

import pytest

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def worker():
    from types import SimpleNamespace
    worker = SimpleNamespace(pid=1)
    return worker


@pytest.fixture
def req():
    from types import SimpleNamespace
    req = SimpleNamespace(headers={"HTTP_X_REQUEST_START": "1234123434"})
    return req


def test_gunicorn_doesnt_crash_with_invalid_settings(env_invalid_missing_dyno, worker, req):
    from dynoscale.hooks.gunicorn import GunicornHookProcessor
    g = GunicornHookProcessor()
    g.pre_request(worker, req)


def test_gunicorn_doesnt_crash_with_valid_settings(env_valid, worker, req):
    from dynoscale.hooks.gunicorn import GunicornHookProcessor
    g = GunicornHookProcessor()
    g.pre_request(worker, req)


def test_gunicorn_pre_request_doesnt_crash_with_valid_settings(env_invalid_missing_dyno, worker, req):
    from dynoscale.hooks.gunicorn import GunicornHookProcessor
    g = GunicornHookProcessor()
    g.pre_request(worker, req)


def test_gunicorn_pre_request_doesnt_crash_with_invalid_settings(env_valid, worker, req):
    from dynoscale.hooks.gunicorn import GunicornHookProcessor
    g = GunicornHookProcessor()
    g.pre_request(worker, req)

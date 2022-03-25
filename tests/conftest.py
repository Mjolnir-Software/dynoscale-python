import os
import signal
import threading
import uuid

import pytest
import responses
from redislite import Redis as Redislite

from dynoscale.agent import DynoscaleAgent
from dynoscale.constants import *
from dynoscale.repository import DynoscaleRepository


# @pytest.fixture(autouse=True)
def on_exit_tear_down_threads():
    yield None
    for thread in [t for t in threading.enumerate() if t != threading.main_thread()]:
        thread.join(0)


@pytest.fixture()
def mock_url():
    return f"https://api.org/{uuid.uuid4()}"


# Environment variables
@pytest.fixture
def env_set_dyno_web1(monkeypatch):
    monkeypatch.setenv(ENV_HEROKU_DYNO, 'web.1')


@pytest.fixture
def env_set_dyno_web2(monkeypatch):
    monkeypatch.setenv(ENV_HEROKU_DYNO, 'web.2')


@pytest.fixture
def env_set_dyno_run9(monkeypatch):
    monkeypatch.setenv(ENV_HEROKU_DYNO, 'run.9')


@pytest.fixture
def env_set_dyno_release1(monkeypatch):
    monkeypatch.setenv(ENV_HEROKU_DYNO, 'release.1')


@pytest.fixture
def env_set_redis_url_localhost(monkeypatch):
    monkeypatch.setenv(ENV_REDIS_URL, 'redis://127.0.0.1:6379')


@pytest.fixture
def env_set_redis_url_all(monkeypatch):
    monkeypatch.setenv(ENV_REDIS_URL, 'redis://127.0.0.1:6379')
    monkeypatch.setenv(ENV_REDISGREEN_URL, 'redis://127.0.0.1:6379')
    monkeypatch.setenv(ENV_REDISTOGO_URL, 'redis://127.0.0.1:6379')
    monkeypatch.setenv(ENV_REDISCLOUD_URL, 'redis://127.0.0.1:6379')
    monkeypatch.setenv(ENV_OPENREDIS_URL, 'redis://127.0.0.1:6379')


@pytest.fixture
def env_del_dyno(monkeypatch):
    monkeypatch.delenv(ENV_HEROKU_DYNO, raising=False)


@pytest.fixture
def env_set_dynoscale_url(monkeypatch, mock_url):
    monkeypatch.setenv(ENV_DYNOSCALE_URL, mock_url)


@pytest.fixture
def env_del_dynoscale_url(monkeypatch):
    monkeypatch.delenv(ENV_DYNOSCALE_URL, raising=False)


@pytest.fixture
def env_del_redis_url(monkeypatch):
    monkeypatch.delenv(ENV_REDIS_URL, raising=False)


@pytest.fixture
def env_del_redis_all(monkeypatch):
    monkeypatch.delenv(ENV_REDIS_URL, raising=False)
    monkeypatch.delenv(ENV_REDIS_URL, raising=False)
    monkeypatch.delenv(ENV_REDISGREEN_URL, raising=False)
    monkeypatch.delenv(ENV_REDISTOGO_URL, raising=False)
    monkeypatch.delenv(ENV_REDISCLOUD_URL, raising=False)
    monkeypatch.delenv(ENV_OPENREDIS_URL, raising=False)


@pytest.fixture
def env_valid(env_set_dyno_web1, env_set_dynoscale_url):
    pass


@pytest.fixture
def env_invalid(env_del_dyno, env_del_dynoscale_url):
    pass


@pytest.fixture
def env_set_dev_mode(monkeypatch):
    monkeypatch.setenv(ENV_DEV_MODE, "")


@pytest.fixture
def env_set_dev_mode_true(monkeypatch):
    monkeypatch.setenv(ENV_DEV_MODE, 'true')


@pytest.fixture
def env_set_dev_mode_1(monkeypatch):
    monkeypatch.setenv(ENV_DEV_MODE, '1')


@pytest.fixture
def env_del_dev_mode(monkeypatch):
    monkeypatch.delenv(ENV_DEV_MODE, raising=False)


# others
@pytest.fixture
def repo_path(tmp_path_factory):
    yield tmp_path_factory.mktemp("data").joinpath("test.sqlite3")


@pytest.fixture
def ds_repository(repo_path) -> DynoscaleRepository:
    dynoscale_repository = DynoscaleRepository(path=repo_path)
    yield dynoscale_repository


@pytest.fixture
def ds_publisher(env_valid, repo_path):
    from dynoscale.publisher import DynoscalePublisher
    yield DynoscalePublisher(repository_path=repo_path)


@pytest.fixture
def ds_agent(env_valid, repo_path):
    from dynoscale.agent import DynoscaleAgent
    yield DynoscaleAgent(repository_path=repo_path)


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mocked_api_200_no_config(mock_url):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, mock_url, status=200)
        yield rsps


@pytest.fixture
def mocked_api_200_with_publish_frequency_30(mock_url):
    with responses.RequestsMock() as rsps:
        payload = {
            'config': {
                'publish_frequency': 30
            }
        }
        rsps.add(responses.POST, mock_url, status=200, json=payload)
        yield rsps


@pytest.fixture
def ds_event_logger(repo_path, env_valid, ds_repository) -> DynoscaleAgent:
    ds_agent = DynoscaleAgent(repository_path=repo_path)
    return ds_agent


@pytest.fixture
def env_set_redis_url_redislite(monkeypatch, redislite_url):
    monkeypatch.setenv(ENV_REDIS_URL, redislite_url)


@pytest.fixture
def redislite_db_path(tmp_path_factory):
    yield tmp_path_factory.mktemp("data").joinpath("redis.db")


@pytest.fixture
def redislite_db_port():
    return 46379


@pytest.fixture
def redislite_url(redislite_db_port):
    return f"redis://127.0.0.1:{redislite_db_port}"


@pytest.fixture
def redislite(redislite_db_path, redislite_db_port) -> Redislite:
    rc = Redislite(redislite_db_path, serverconfig={'port': f"{redislite_db_port}"})
    yield rc
    rc.close()
    rc.shutdown()
    # os.kill(rc.pid, signal.SIGTERM)

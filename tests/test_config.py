import logging
from contextlib import nullcontext as does_not_raise

import pytest

from dynoscale.config import Config

logging.basicConfig(level=logging.DEBUG)


def test_config_does_not_crash_with_missing_env_vars(env_invalid):
    Config()


def test_config_with_valid_environ_vars_is_valid(env_valid):
    assert Config().is_valid


def test_config_with_dyno_missing_in_environ_is_invalid(env_set_dynoscale_url, env_del_dyno):
    assert not Config().is_valid


def test_config_with_dynoscale_url_missing_in_environ_is_invalid(env_set_dyno_web1, env_del_dynoscale_url):
    assert not Config().is_valid


def test_config_with_valid_env_vars_and_dev_mode_is_valid(env_valid):
    assert Config().is_valid


def test_config_with_invalid_env_vars_and_dev_mode_is_invalid(env_invalid, monkeypatch):
    c = Config()
    assert not c.is_valid


# noinspection HttpUrlsUsage
@pytest.mark.parametrize(
    "dyno,url,is_valid, expectation",
    [
        # valid
        ("web.1", "http://api.io", True, does_not_raise()),
        ("web.1", "http://api.io/", True, does_not_raise()),
        ("web.1", "http://api.io/http", True, does_not_raise()),
        ("dyno.1", "https://api.io/https", True, does_not_raise()),
        ("dyno.1", "https://api.io/https/deep", True, does_not_raise()),
        ("dyno.1", "https://api.io/https/deep/", True, does_not_raise()),
        ("dyno.1", "https://api.io/https/deep/?param", True, does_not_raise()),
        ("dyno.1", "https://api.io/https/deep/?param=value", True, does_not_raise()),
        ("dyno.1", "https://api.io/?param=%F0%9F%91%8D%21%40%23%24%25%5E%26%2A%28%29", True, does_not_raise()),
        ("dyno.1", "https://api.io?param=%F0%9F%91%8D%21%40%23%24%25%5E%26%2A%28%29", True, does_not_raise()),
        ("dyno.1", "https://api.io/https/deep/?param#anchor", True, does_not_raise()),
        ("run.1", "http://api.io/https", True, does_not_raise()),
        ("run.1", "http://api.io:3333/https", True, does_not_raise()),
        ("worker.1", "https://user:password@api.io", True, does_not_raise()),
        ("worker.1", "https://api.io", True, does_not_raise()),

        # invalid
        (None, None, False, does_not_raise()),
        ("", None, False, does_not_raise()),
        (None, "", False, does_not_raise()),
        ("", "", False, does_not_raise()),
        ("web.1", None, False, does_not_raise()),
        ("web.1", "", False, does_not_raise()),
        ("web.1", "not_an_url", False, does_not_raise()),
        ("web.1", "http:/also.not", False, does_not_raise()),
        ("web.1", "http: //also.not", False, does_not_raise()),
        ("web.1", "http:// also.not", False, does_not_raise()),
        ("web.1", "http://also,not", False, does_not_raise()),
        ("web.1", "http://also;not", False, does_not_raise()),
        (None, "https://good.url/", False, does_not_raise()),
        ("", "https://api.io/https", False, does_not_raise()),
        ("web.2", "https://api.io/https", False, does_not_raise()),
        ("run.2", "https://api.io/https", False, does_not_raise()),
        ("dyno.1", "", False, does_not_raise()),
        ("run.999", "", False, does_not_raise()),
        ("dyno.1", "", False, does_not_raise()),
        ("run.1", "", False, does_not_raise()),
        # ([], pytest.raises(ZeroDivisionError)),
    ],
)
def test_config_with_env_vars(env_invalid, monkeypatch, dyno, url, is_valid, expectation):
    from dynoscale.constants import ENV_DYNOSCALE_URL
    from dynoscale.constants import ENV_HEROKU_DYNO
    if dyno is not None:
        monkeypatch.setenv(ENV_HEROKU_DYNO, dyno)
    if url is not None:
        monkeypatch.setenv(ENV_DYNOSCALE_URL, url)
    with expectation:
        config = Config()
        assert config.is_valid == is_valid

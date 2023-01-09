import json
import os
from enum import Enum
from typing import Dict

from dynoscale.constants import *
from dynoscale.repository import DEFAULT_DYNOSCALE_REPOSITORY_FILENAME
from dynoscale.utils import is_valid_url, ensure_module


def get_redis_urls_from_environ() -> Dict[str, str]:
    """Returns a dictionary of possible redis urls from all known redis_url environment variables"""
    redis_env_vars = (ENV_REDIS_URL, ENV_REDISTOGO_URL, ENV_OPENREDIS_URL, ENV_REDISGREEN_URL, ENV_REDISCLOUD_URL)
    return {name: os.environ[name] for name in redis_env_vars if name in os.environ}


class RunMode(Enum):
    PRODUCTION = 1
    DEVELOPMENT = 2


class Config:

    @property
    def is_valid(self) -> bool:
        if not (self.dyno and isinstance(self.dyno, str) and self.dyno.endswith('.1')):
            return False
        if not (self.url and isinstance(self.url, str) and is_valid_url(self.url)):
            return False
        return True

    @property
    def is_not_valid(self) -> bool:
        return not self.is_valid

    @property
    def run_mode_name(self):
        return RunMode.DEVELOPMENT.name if self.is_dev_mode else RunMode.PRODUCTION.name

    @property
    def is_rq_available(self) -> bool:
        return ensure_module('rq') is not None and ensure_module('redis') is not None and self.redis_urls

    @property
    def repository_path(self) -> bytes:
        return os.path.join(self.repository_dir_name, self.repository_file_name)

    def __init__(self):
        self.is_dev_mode = bool(os.environ.get(ENV_DEV_MODE, False))
        self.dyno = os.environ.get(ENV_HEROKU_DYNO)
        self.url = os.environ.get(ENV_DYNOSCALE_URL)
        self.redis_urls = get_redis_urls_from_environ()
        self.repository_dir_name = os.environ.get(ENV_DYNOSCALE_DATA_DIR_NAME, os.getcwd())
        self.repository_file_name = os.environ.get(ENV_DYNOSCALE_DATA_FILE_NAME, DEFAULT_DYNOSCALE_REPOSITORY_FILENAME)

    def __repr__(self) -> str:
        obj = {
            ENV_DEV_MODE: self.is_dev_mode,
            ENV_HEROKU_DYNO: self.dyno,
            ENV_DYNOSCALE_URL: self.url,
            'redis_urls': self.redis_urls,
            'repository_path': self.repository_path
        }
        return json.dumps(obj, skipkeys=True, sort_keys=True)

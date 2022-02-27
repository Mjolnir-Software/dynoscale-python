import json
import os
from enum import Enum

from dynoscale.constants import ENV_DEV_MODE, ENV_HEROKU_DYNO, ENV_DYNOSCALE_URL
from dynoscale.utils import is_valid_url


class RunMode(Enum):
    PRODUCTION = 1
    DEVELOPMENT = 2


class Config:

    @property
    def run_mode_name(self):
        return RunMode.DEVELOPMENT.name if self.is_dev_mode else RunMode.PRODUCTION.name

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

    def __init__(self):
        self.is_dev_mode = bool(os.environ.get(ENV_DEV_MODE, False))
        self.dyno = os.environ.get(ENV_HEROKU_DYNO)
        self.url = os.environ.get(ENV_DYNOSCALE_URL)

    def __repr__(self) -> str:
        obj = {ENV_DEV_MODE: self.is_dev_mode,
               ENV_HEROKU_DYNO: self.dyno,
               ENV_DYNOSCALE_URL: self.url
               }
        return json.dumps(obj, skipkeys=True, sort_keys=True)

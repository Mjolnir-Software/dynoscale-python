import logging
from typing import Callable

from dynoscale.agent import DynoscaleAgent
from dynoscale.config import Config
from dynoscale.constants import HTTP_X_REQUEST_START
from dynoscale.utils import epoch_ms, get_int_from_headers, fake_request_start_ms


class DynoscaleWsgiApp:

    def __init__(self, app):
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{DynoscaleWsgiApp.__name__}")
        self.logger.debug("__init__")
        self.__app = app

        self.config = Config()
        if self.config.is_not_valid:
            self.logger.warning(f"{DynoscaleWsgiApp.__name__} will not "
                                f"initialize {DynoscaleAgent.__name__} with invalid config: {self.config}.")
            return  # User app will keep running, but queue times won't be logged
        self.ds_agent = DynoscaleAgent()
        self.logger.info(f"{DynoscaleWsgiApp.__name__} started in {self.config.run_mode_name} mode.")

    def __call__(self, environ: dict, start_response: Callable):
        # Under no circumstances should we ever stop user's app from receiving the request
        try:
            self.logger.debug("__call__")
            if self.config.is_valid:
                self.log_queue_time(environ)
        except Exception:
            self.logger.error("Unknown error, while processing Wsgi __call__")
        finally:
            return self.__app(environ, start_response)

    def log_queue_time(self, environ):
        # Under no circumstances should we ever stop user app from receiving the request
        try:
            self.logger.debug(f"log_queue_time (e:{environ})")
            log_start = epoch_ms()
            http_x_request_start = get_int_from_headers(
                environ,
                HTTP_X_REQUEST_START,
                fake_request_start_ms() if self.config.is_dev_mode else None
            )
            if http_x_request_start is not None:
                req_queue_time: int = log_start - http_x_request_start
                req_timestamp = int(log_start / 1_000)
                self.logger.debug(f"log_queue_time - Logging queue time {req_queue_time}")
                self.ds_agent.log_queue_time(req_timestamp, req_queue_time)
            else:
                self.logger.info("Can not calculate queue time.")
        except Exception as e:
            self.logger.error(f"Unknown error while attempting to log a queue time: {e}")

import logging

from dynoscale.agent import DynoscaleAgent
from dynoscale.config import Config
from dynoscale.constants import X_REQUEST_START
from dynoscale.utils import epoch_ms, get_int_from_headers, fake_request_start_ms

PROC_NAME = '__dynoscale_hook_processor'

logger = logging.getLogger(__name__)


def pre_request(worker, req):
    logger.debug(f"pre_request - {worker} {req}")
    processor = globals().get(PROC_NAME, None)
    if processor is None:
        processor = GunicornHookProcessor()
        globals()[PROC_NAME] = processor
    processor.pre_request(worker, req)


class GunicornHookProcessor:

    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{GunicornHookProcessor.__name__}")
        self.config = Config()
        if self.config.is_valid:
            self.logger.info(f"Dynoscale started {GunicornHookProcessor.__name__} in {self.config.run_mode_name} mode.")
            self.ds_agent = DynoscaleAgent()
        else:
            self.logger.warning(
                f"Dynoscale can't start {GunicornHookProcessor.__name__} with invalid config: {self.config}."
            )
            return

    def pre_request(self, worker, req):
        # Under no circumstances should we ever stop user app from receiving the request
        try:
            self.logger.debug(f"pre_request (w:{id(worker)} w.pid{worker.pid} rq:{id(req)})")
            log_start: int = epoch_ms()
            http_x_request_start = get_int_from_headers(
                req.headers,
                X_REQUEST_START,
                fake_request_start_ms() if self.config.is_dev_mode else None
            )
            if http_x_request_start is not None:
                req_queue_time: int = log_start - http_x_request_start
                req_timestamp = int(log_start / 1_000)
                self.logger.debug(f"pre_request - Logging queue time: {req_queue_time}")
                self.ds_agent.log_queue_time(req_timestamp, req_queue_time)
            else:
                self.logger.info("Can not calculate queue time.")
        except Exception as e:
            self.logger.error(f"Unknown error while attempting to log a queue time: {e}")

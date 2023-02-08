import logging
import queue
import threading

from dynoscale.config import Config
from dynoscale.publisher import DynoscalePublisher
from dynoscale.repository import Record

RECORD_SOURCE = "web"
RECORD_METADATA = ""

logger = logging.getLogger(__name__)
request_log_queue = queue.Queue()


def queue_time_logger(enable_rq_logger: bool):
    logger.debug("queue_time_logger")
    publisher = DynoscalePublisher()
    if enable_rq_logger:
        from dynoscale.workers.rq_logger import DynoscaleRqLogger
        rq_logger = DynoscaleRqLogger()
        publisher.pre_publish_hook = rq_logger.log_queue_times

    while True:
        record: Record = request_log_queue.get(block=True, timeout=None)
        logger.debug(f"queue_time_logger - got record from queue: {record}")
        publisher.repository.add_record(record)
        logger.info(f"Queue time {record.metric}ms logged at {record.timestamp}.")
        publisher.tick()


class DynoscaleAgent:

    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{DynoscaleAgent.__name__}")
        self.logger.debug("__init__")
        self.config = Config()
        if self.config.is_valid:
            self.t_logger = threading.Thread(
                target=queue_time_logger,
                daemon=True,
                kwargs={
                    'enable_rq_logger': self.config.is_rq_available,
                },
                name='Dynoscale'
            )
            self.t_logger.start()
            self.logger.info(f"Logging thread '{self.t_logger.name}' started.")
        else:
            self.logger.warning(
                f"{DynoscaleAgent.__name__} will not start Dynoscale logger thread with invalid config: {self.config}."
            )

    def log_queue_time(self, timestamp: int, queue_time: int):
        self.logger.debug(f"log_queue_time - {timestamp} {queue_time}")
        if self.config.is_valid:
            record = Record(timestamp, queue_time, RECORD_SOURCE, RECORD_METADATA)
            try:
                request_log_queue.put(record, timeout=0.25)
            except queue.Full:
                self.logger.error(f"Log queue is full, record {record} won't be logged!")
        else:
            self.logger.info(f"Throwing away queue time due to invalid config: {self.config}")

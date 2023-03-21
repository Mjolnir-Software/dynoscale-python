import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Iterable, Generator

import redis
from rq import Queue

from dynoscale.config import Config, get_redis_urls_from_environ
from dynoscale.repository import DynoscaleRepository, Record
from dynoscale.utils import epoch_s

logger = logging.getLogger(__name__)


def get_enqueued_at_of_oldest_job(queue: Queue) -> Optional[datetime]:
    jobs = queue.get_jobs(offset=0, length=1)
    return jobs[0].enqueued_at if jobs else None


def queue_time_records_for_connection(connection) -> Iterable[Record]:
    utc_now = datetime.utcnow()
    for queue in Queue.all(connection=connection):
        logger.debug(f"Dynoscale getting oldest RQ job for queue: {queue.name}")
        oldest_job_enqueued_at = get_enqueued_at_of_oldest_job(queue)
        if oldest_job_enqueued_at is not None:
            queue_time_ms = int((utc_now - oldest_job_enqueued_at).total_seconds() * 1_000)
            yield Record(timestamp=epoch_s(), metric=queue_time_ms, source=f"rq:{queue.name}", metadata="")


@contextmanager
def redis_connection(url: str) -> Generator[redis.Redis, None, None]:
    conn = None
    try:
        conn = redis.from_url(url)
        yield conn
    finally:
        if conn:
            conn.close()


def get_queue_time_records() -> Iterable[Record]:
    for url_name, redis_url in get_redis_urls_from_environ().items():
        try:
            with redis_connection(redis_url) as conn:
                logger.debug(f"Dynoscale getting RQ queue time records from Redis@{redis_url}")
                for record in queue_time_records_for_connection(conn):
                    yield record
        except Exception as e:
            logger.warning(f"Dynoscale caught exception while getting queue times: {e}")


class DynoscaleRqLogger:
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{DynoscaleRqLogger.__name__}")
        self.logger.debug("DynoscaleRqLogger initializing...")
        self.config = Config()
        if not self.config.is_rq_available:
            self.logger.warning("Rq not available, DynoscaleRqLogger will not initialize.")
            return
        self.repository = DynoscaleRepository(self.config.repository_path)

    def log_queue_times(self):
        try:  # Under no circumstances should log_queue_times crash
            if not self.config.is_rq_available:
                self.logger.error("Rq not available, can't log RQ worker queue times.")
                return
            for record in get_queue_time_records():
                try:
                    self.logger.debug(f"DynoscaleRqLogger adding record: {record}")
                    self.repository.add_record(record)
                except Exception as e:
                    logger.warning(f"DynoscaleRqLogger couldn't add record: {record} exception: {e} ")
        except Exception as e:
            logger.warning(f"DynoscaleRqLogger couldn't get queue times: {e} ")

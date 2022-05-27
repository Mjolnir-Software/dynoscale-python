import datetime
import logging
import os
from contextlib import contextmanager
from typing import Optional, Union, Iterable, Generator

import redis
from rq import Queue
from rq.job import Job

from dynoscale.config import Config, get_redis_urls_from_environ
from dynoscale.repository import DynoscaleRepository, Record
from dynoscale.utils import epoch_s

logger = logging.getLogger(__name__)


def get_oldest_queued_job(queue) -> Optional[Job]:
    queued_jobs = [job for job in queue.jobs if job.is_queued]
    sorted_jobs = sorted(queued_jobs, key=lambda job: job.enqueued_at)
    return sorted_jobs[0] if sorted_jobs else None


def queue_time_records_for_connection(connection) -> Iterable[Record]:
    for queue in Queue.all(connection=connection):
        logger.debug(f"Dynoscale getting oldest RQ job for queue: {queue.name}")
        oldest_job = get_oldest_queued_job(queue)
        if oldest_job is not None:
            queue_time_ms = int((datetime.datetime.utcnow() - oldest_job.enqueued_at).total_seconds() * 1000)
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
    def __init__(self, repository_path: Optional[Union[str, bytes, os.PathLike]] = None):
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{DynoscaleRqLogger.__name__}")
        self.logger.debug("DynoscaleRqLogger initializing...")
        self.config = Config()
        if not self.config.is_rq_available:
            self.logger.warning("Rq not available, DynoscaleRqLogger will not initialize.")
            return
        self.repository = DynoscaleRepository(repository_path)

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

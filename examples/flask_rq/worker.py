import os
import time

import redis
from rq import Worker, Queue, Connection

from dynoscale.workers.rq_logger import allow_self_signed_certificates

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--redis_url",
        type=str,
        help="Redis Url for RQ, default: %(default)s",
        default='redis://127.0.0.1:6379'
    )
    parser.add_argument(
        "--redis_url_in",
        type=str,
        help="Env var with Redis Url for RQ, default: %(default)s",
        default='REDIS_TLS_URL'
    )
    args = parser.parse_args()

    redis_url = allow_self_signed_certificates(os.getenv(args.redis_url_in, args.redis_url))
    print(f"Starting RQ worker, will connect to redis @ {redis_url}")
    conn = redis.from_url(redis_url)
    with Connection(conn):
        Worker(list(map(Queue, ['urgent', 'priority', 'default']))).work()


def count_cycles_and_wait_a_bit(duration: float) -> str:
    start = time.time()
    cycle_count = 0
    while time.time() < start + duration:
        time.sleep(0.001)
        cycle_count += 1
    return f"I managed to run the loop {cycle_count} times in the allotted {duration}s."

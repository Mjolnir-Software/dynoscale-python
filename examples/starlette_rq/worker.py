import math
import os
import time

import redis
from rq import Worker, Queue, Connection

from dynoscale.config import get_redis_urls_from_environ

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
        default='REDIS_URL'
    )
    args = parser.parse_args()

    redis_url = os.getenv(args.redis_url_in, args.redis_url)
    if redis_url is None:
        urls_from_env = list(get_redis_urls_from_environ().values())
        redis_url = urls_from_env[0] if urls_from_env else 'redis://127.0.0.1:6379'

    print(f"Starting RQ worker, will connect to redis @ {redis_url}")
    conn = redis.from_url(redis_url)
    with Connection(conn):
        Worker(list(map(Queue, ['urgent', 'priority', 'default']))).work()


def count_cycles_and_wait_a_bit(duration: float) -> str:
    start = time.time()
    cycle_count = 0
    atan_sum = 0
    while time.time() < start + duration:
        atan_sum += sum([math.atan(time.time()) for _ in range(10_000)])
        time.sleep(0.0001)
        cycle_count += 1
    return f"In the allotted {duration}s I did {cycle_count} loops and calculated the atan_sum to be {atan_sum}."

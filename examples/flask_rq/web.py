import logging
import os
import sys
import time
from typing import Optional

import colorlog
import redis
from flask import Flask, request, render_template
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

from dynoscale.config import get_redis_urls_from_environ
from dynoscale.workers.rq_logger import allow_self_signed_certificates
from dynoscale.wsgi import DynoscaleWsgiApp
from worker import count_cycles_and_wait_a_bit

# Configure logging
handler = colorlog.StreamHandler(stream=sys.stdout)
handler.setFormatter(
    colorlog.ColoredFormatter(
        fmt="%(asctime)s.%(msecs)03d %(log_color)s%(levelname)-8s%(reset)s %(processName)s %(threadName)10s"
            " %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
)
logging.getLogger("").handlers = [handler]
logging.getLogger("dynoscale").setLevel(logging.DEBUG)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


def get_hit_count():
    retries = 5
    while True:
        try:
            return conn.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


@app.route('/')
def index():
    queue_name = request.args.get('queue_name')
    job_count = request.args.get('job_count', type=int, default=1)
    jobs = None
    if queue_name == 'urgent':
        jobs = q_urgent.enqueue_many(
            [Queue.prepare_data(func=count_cycles_and_wait_a_bit, kwargs={'duration': 1.0}) for _ in range(job_count)]
        )
    elif queue_name == 'priority':
        jobs = q_priority.enqueue_many(
            [Queue.prepare_data(func=count_cycles_and_wait_a_bit, kwargs={'duration': 3.0}) for _ in range(job_count)]
        )
    elif queue_name == 'default':
        jobs = q_default.enqueue_many(
            [Queue.prepare_data(func=count_cycles_and_wait_a_bit, kwargs={'duration': 5.0}) for _ in range(job_count)]
        )
    return render_template(
        'index.html',
        hit_count=get_hit_count(),
        job_count=job_count,
        jobs=jobs,
        q_urgent=q_urgent,
        q_default=q_default,
        q_priority=q_priority
    )


@app.route("/jobs/<job_id>", methods=['GET'])
def job_detail(job_id):
    job = None
    try:
        job = Job.fetch(job_id, connection=conn)
    except NoSuchJobError:
        logging.getLogger().warning(f"Job with id {job_id} does not exist!")
    finally:
        return render_template('job_detail.html', job=job)


def init_redis_conn_and_queues(redis_url: Optional[str] = None):
    if redis_url is None:
        urls_from_env = list(get_redis_urls_from_environ().values())
        redis_url = urls_from_env[0] if redis_url else 'redis://127.0.0.1:6379'
    global conn
    global q_urgent
    global q_priority
    global q_default
    conn = redis.from_url(allow_self_signed_certificates(redis_url))
    q_urgent = Queue('urgent', connection=conn)
    q_priority = Queue('priority', connection=conn)
    q_default = Queue(connection=conn)


if __name__ == "__main__":
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

    redis_url = os.getenv(args.redis_url_in, args.redis_url)
    init_redis_conn_and_queues(redis_url)

    print(f"Starting Flask server, sending RQ jobs to redis @ {redis_url}")
    app.wsgi_app = DynoscaleWsgiApp(app.wsgi_app)
    port = os.getenv('PORT', 3000)
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    init_redis_conn_and_queues()

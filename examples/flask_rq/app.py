import logging
import os
import sys
import time

import colorlog
import redis
from flask import Flask, request, render_template
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job

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
logging.getLogger("dynoscale").setLevel(logging.INFO)

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
    job = None
    if queue_name == 'urgent':
        job = q_urgent.enqueue_call(
            func=count_cycles_and_wait_a_bit,
            kwargs={'duration': 1.0},
        )
    elif queue_name == 'priority':
        job = q_priority.enqueue_call(
            func=count_cycles_and_wait_a_bit,
            kwargs={'duration': 3.0},
        )
    elif queue_name == 'default':
        job = q_default.enqueue_call(
            func=count_cycles_and_wait_a_bit,
            kwargs={'duration': 5.0},
        )
    return render_template(
        'index.html',
        hit_count=get_hit_count(),
        job=job,
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


def init_redis_conn_and_queues(redis_url: str = 'redis://127.0.0.1:6379'):
    global conn
    global q_urgent
    global q_priority
    global q_default
    conn = redis.from_url(redis_url)
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
        default='REDIS_URL'
    )
    args = parser.parse_args()

    redis_url = os.getenv(args.redis_url_in, args.redis_url)
    init_redis_conn_and_queues(redis_url)

    print(f"Starting Flask server, sending RQ jobs to redis @ {redis_url}")
    app.wsgi_app = DynoscaleWsgiApp(app.wsgi_app)
    app.run(host='127.0.0.1', port=3000, debug=True)
else:
    init_redis_conn_and_queues()

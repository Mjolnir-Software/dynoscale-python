import logging
import os
import sys
import time
from typing import Optional

import colorlog
import redis
import uvicorn
from asgiref.typing import ASGI3Application
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job
from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from dynoscale.asgi import DynoscaleASGIApp
from dynoscale.config import get_redis_urls_from_environ
from worker import count_cycles_and_wait_a_bit

templates = Jinja2Templates(directory='./templates')


async def favicon(request):
    return FileResponse("./favicon.ico")


async def index(request):
    queue_name = request.query_params.get('queue_name')
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
    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'job': job,
            'q_urgent': q_urgent,
            'q_default': q_default,
            'q_priority': q_priority,
            'hit_count': get_hit_count(),
        }
    )


async def jobs(request):
    job_id = request.path_params.get('job_id')
    job = None
    try:
        job = Job.fetch(job_id, connection=conn)
    except NoSuchJobError:
        logging.getLogger().warning(f"Job with id {job_id} does not exist!")
    finally:
        return templates.TemplateResponse(
            'job_detail.html',
            {
                'request': request,
                'job': job
            }
        )


routes = [
    Route("/favicon.ico", endpoint=favicon, methods=['GET']),
    Route("/jobs/{job_id:str}", endpoint=jobs, methods=['GET']),
    Route('/', endpoint=index, methods=['GET'])
]

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

app: ASGI3Application = Starlette(debug=True, routes=routes)


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


def init_redis_conn_and_queues(redis_url: Optional[str] = None):
    if redis_url is None:
        urls_from_env = list(get_redis_urls_from_environ().values())
        redis_url = urls_from_env[0] if redis_url else 'redis://127.0.0.1:6379'
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

    print(f"Starting Starlette server, sending RQ jobs to redis @ {redis_url}")
    uvicorn.run(DynoscaleASGIApp(app), port=os.getenv('PORT', 8000), log_level="info")
else:
    init_redis_conn_and_queues()

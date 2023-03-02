import datetime
import gc
import math
import time
import timeit
from sys import getsizeof

from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route


def waste_cpu() -> float:
    return sum([math.atan2(math.sin(i), math.cos(i + 1)) for i in range(1, 10_000)])


def waste_ram(megs: int = 16) -> int:
    # Allocate and immediately release 32MB of RAM by default
    foo = bytes("?" * (megs * 2 ** 20 - 33), 'utf-8')
    wasted_memory = getsizeof(foo)
    del foo
    gc.collect()
    return wasted_memory


def waste_io(seconds: float = 0.01) -> float:
    start = time.time()
    if time:
        time.sleep(seconds)
    return time.time() - start


def waste_resources(cpu: int = 0, ram: int = 0, io: int = 0) -> str:
    wasted_io = 0
    wasted_ram = 0
    wasted_cpu = 0
    if cpu:
        wasted_cpu += timeit.timeit(lambda: waste_cpu(), number=cpu)
    if ram:
        wasted_ram += timeit.timeit(lambda: waste_ram(), number=ram)
    if io:
        wasted_io += timeit.timeit(lambda: waste_io(), number=io)
    return f"Successfully wasted {wasted_cpu}s on CPU tasks, {wasted_ram}s on RAM and {wasted_io}s waiting for IO."


async def route_index(_):
    return Response(
        "Hello from 🌟 Starlette 🌟 served by Gunicorn using Uvicorn workers and scaled by Dynoscale!\n"
        f"It's {datetime.datetime.now()} right now.",
        media_type='text/plain'
    )


async def route_cpu(request):
    return Response(
        waste_resources(cpu=request.path_params.get('loop_count', 0)),
        media_type='text/plain'
    )


async def route_ram(request):
    return Response(
        waste_resources(ram=request.path_params.get('loop_count', 0)),
        media_type='text/plain'
    )


async def route_io(request):
    return Response(
        waste_resources(io=request.path_params.get('loop_count', 0)),
        media_type='text/plain'
    )


app = Starlette(
    debug=True,
    routes=[
        Route('/', route_index),
        Route('/cpu', route_cpu),
        Route('/ram', route_ram),
        Route('/io', route_io),
        Route('/cpu/{loop_count:int}', route_cpu),
        Route('/ram/{loop_count:int}', route_ram),
        Route('/io/{loop_count:int}', route_io),
    ]
)

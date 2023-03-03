import datetime
import gc
import math
import time
import timeit
from sys import getsizeof
from textwrap import dedent

import starlette.requests
from starlette.applications import Starlette
from starlette.responses import Response, HTMLResponse, PlainTextResponse
from starlette.routing import Route


def waste_io(millis: int = 10) -> float:
    start = time.time()
    if time:
        time.sleep(millis / 1000.0)
    return time.time() - start


def waste_cpu() -> float:
    return sum([math.atan2(math.sin(i), math.cos(i + 1)) for i in range(1, 10_000)])


def waste_ram(megs: int = 16) -> int:
    # Allocate and immediately release RAM
    waste = bytes("?" * (megs * 2 ** 20 - 33), 'utf-8')
    wasted_memory = getsizeof(waste)
    return wasted_memory


def waste_gc(megs: int = 0) -> int:
    # Optionally allocate and release but always garbage collect
    wasted_memory = 0
    if megs:
        waste = bytes("?" * (megs * 2 ** 20 - 33), 'utf-8')
        wasted_memory = getsizeof(waste)
        del waste
    gc.collect()
    return wasted_memory


def waste_resources(io: int = 0, cpu: int = 0, ram: int = 0, garbage: int = 0) -> str:
    wasted_io = 0
    wasted_ram = 0
    wasted_gc = 0
    wasted_cpu = 0
    if cpu:
        wasted_cpu += timeit.timeit(lambda: waste_cpu(), number=cpu)
    if ram:
        wasted_ram += timeit.timeit(lambda: waste_ram(ram), number=1)
    if garbage:
        wasted_gc += timeit.timeit(lambda: waste_gc(garbage), number=1)
    if io:
        wasted_io += timeit.timeit(lambda: waste_io(io), number=1)
    return f"Wasted {wasted_io:.3f}s waiting, {wasted_cpu:.3f}s on CPU tasks," \
           f" {wasted_ram:.3f}s claiming RAM and {wasted_gc:.3f}s collecting garbage."


async def route_index(_):
    payload = """\
    <html><body>
    <h1>Hello from 🌟 Starlette 🌟 served by Gunicorn using Uvicorn workers and scaled by Dynoscale!</h1>
    <table>
    <tr>
        <td><strong>Waste IO (Waiting)</strong></td>
        <td><a href="/io/1" target="activity"> 1ms</a></td>
        <td><a href="/io/2" target="activity"> 2ms</a></td>
        <td><a href="/io/5" target="activity"> 5ms</a></td>
        <td><a href="/io/10" target="activity"> 10ms</a></td>
        <td><a href="/io/20" target="activity"> 20ms</a></td>
        <td><a href="/io/50" target="activity"> 50ms</a></td>
        <td><a href="/io/100" target="activity"> 100ms</a></td>
        <td><a href="/io/200" target="activity"> 200ms</a></td>
        <td><a href="/io/500" target="activity"> 500ms</a></td>
        <td><a href="/io/1000" target="activity"> 1000ms</a></td>
        <td><a href="/io/2000" target="activity"> 2000ms</a></td>
        <td><a href="/io/5000" target="activity"> 5000ms</a></td>
    </tr>
    <tr>
        <td><strong>Waste CPU (Calculating)</strong></td>
        <td><a href="/cpu/1" target="activity"> 1x</a></td>
        <td><a href="/cpu/2" target="activity"> 2x</a></td>
        <td><a href="/cpu/5" target="activity"> 5x</a></td>
        <td><a href="/cpu/10" target="activity"> 10x</a></td>
        <td><a href="/cpu/20" target="activity"> 20x</a></td>
        <td><a href="/cpu/50" target="activity"> 50x</a></td>
        <td><a href="/cpu/100" target="activity"> 100x</a></td>
        <td><a href="/cpu/200" target="activity"> 200x</a></td>
        <td><a href="/cpu/500" target="activity"> 500x</a></td>
        <td><a href="/cpu/1000" target="activity"> 1000x</a></td>
        <td><a href="/cpu/2000" target="activity"> 2000x</a></td>
        <td><a href="/cpu/5000" target="activity"> 5000x</a></td>
    </tr>
    <tr>
        <td><strong>Waste RAM (Claiming and leaving)</strong></td>
        <td><a href="/ram/1" target="activity"> 1MB</a></td>
        <td><a href="/ram/2" target="activity"> 2MB</a></td>
        <td><a href="/ram/5" target="activity"> 5MB</a></td>
        <td><a href="/ram/10" target="activity"> 10MB</a></td>
        <td><a href="/ram/20" target="activity"> 20MB</a></td>
        <td><a href="/ram/50" target="activity"> 50MB</a></td>
        <td><a href="/ram/100" target="activity"> 100MB</a></td>
        <td><a href="/ram/200" target="activity"> 200MB</a></td>
        <td><a href="/ram/500" target="activity"> 500MB</a></td>
        <td><a href="/ram/1000" target="activity"> 1000MB</a></td>
        <td><a href="/ram/2000" target="activity"> 2000MB</a></td>
        <td><a href="/ram/5000" target="activity"> 5000MB</a></td>
    </tr>
    <tr>
        <td><strong>Waste GC (Claiming, Deleting and Requesting Garbage collection)</strong></td>
        <td><a href="/gc/1" target="activity"> 1MB</a></td>
        <td><a href="/gc/2" target="activity"> 2MB</a></td>
        <td><a href="/gc/5" target="activity"> 5MB</a></td>
        <td><a href="/gc/10" target="activity"> 10MB</a></td>
        <td><a href="/gc/20" target="activity"> 20MB</a></td>
        <td><a href="/gc/50" target="activity"> 50MB</a></td>
        <td><a href="/gc/100" target="activity"> 100MB</a></td>
        <td><a href="/gc/200" target="activity"> 200MB</a></td>
        <td><a href="/gc/500" target="activity"> 500MB</a></td>
        <td><a href="/gc/1000" target="activity"> 1000MB</a></td>
        <td><a href="/gc/2000" target="activity"> 2000MB</a></td>
        <td><a href="/gc/5000" target="activity"> 5000MB</a></td>
    </tr>
    </table>
    <iframe name="activity" src="/date" width="100%"></iframe>
    </body></html>
    """
    return HTMLResponse(dedent(payload))


async def route_date(_):
    return Response(f"It's {datetime.datetime.now()} right now.", media_type='text/plain')


async def route_info(request: starlette.requests.Request):
    payload = ""
    for k, v in request.scope.items():
        payload += f"### {k.upper() + ' ':#<75}\n"
        match v:
            case dict():
                payload += "\n".join(f"{kk:<32}: {vv}" for kk, vv in v.items())
            case list():
                payload += "\n".join(f"{vv}" for vv in v)
            case _:
                payload += f"{v}"
        payload += "\n\n"
    payload += f"### {'BODY' + ' ':#<75}\n"
    payload += (await request.body()).decode('utf-8')
    return PlainTextResponse(payload)


async def route_waste_resources(request):
    sleep_ms = request.path_params.get('sleep_ms', 0)
    loop_count = request.path_params.get('loop_count', 0)
    ram_claim_megs = request.path_params.get('ram_claim_megs', 0)
    gc_claim_megs = request.path_params.get('gc_claim_megs', 0)
    result_text = waste_resources(io=sleep_ms, cpu=loop_count, ram=ram_claim_megs, garbage=gc_claim_megs)
    return Response(result_text, media_type='text/plain')


app = Starlette(
    debug=True,
    routes=[
        Route('/', route_index),
        Route('/date', route_date),
        Route('/info', route_info),
        Route('/io', route_waste_resources),
        Route('/cpu', route_waste_resources),
        Route('/ram', route_waste_resources),
        Route('/gc', route_waste_resources),
        Route('/io/{sleep_ms:int}', route_waste_resources),
        Route('/cpu/{loop_count:int}', route_waste_resources),
        Route('/ram/{ram_claim_megs:int}', route_waste_resources),
        Route('/gc/{gc_claim_megs:int}', route_waste_resources),
    ]
)

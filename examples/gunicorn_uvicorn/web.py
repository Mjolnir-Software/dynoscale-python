#! /usr/bin/env python3
import datetime
import logging
import sys

import colorlog
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

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


async def home(_):
    return Response(
        "Hello from 🌟 Starlette 🌟 served by Gunicorn using Uvicorn workers and scaled by Dynoscale!\n"
        f"It's {datetime.datetime.now()} right now.",
        media_type='text/plain'
    )


app = Starlette(debug=True, routes=[Route('/', endpoint=home, methods=['GET'])])

if __name__ == "__main__":
    import os
    import subprocess

    ps_name = 'gunicorn'
    my_env = os.environ.copy()

    my_env["DYNO"] = "web.1"
    my_env["DYNOSCALE_DEV_MODE"] = "true"
    my_env["DYNOSCALE_URL"] = "https://eo9c4z6r0y3jssb.m.pipedream.net"

    print(f"Starting subprocess '{ps_name}'...")
    proc = subprocess.Popen(ps_name)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nXXXXXXXXXXXXXXXX web.py received interrupt: <Ctrl-C> XXXXXXXXXXXXXXXX\n")
        print(f"Stopping subprocess '{ps_name}'...")
        proc.terminate()
    finally:
        proc.wait(timeout=5.0)
        print(f"Subprocess '{ps_name}' stopped.")
        exit(0)

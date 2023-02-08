import datetime
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route


async def home(_):
    return Response(
        "Hello from 🌟 Starlette 🌟 served by Gunicorn using Uvicorn workers and scaled by Dynoscale!\n"
        f"It's {datetime.datetime.now()} right now.",
        media_type='text/plain'
    )


app = Starlette(debug=True, routes=[Route('/', endpoint=home, methods=['GET'])])

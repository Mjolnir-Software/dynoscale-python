import os

from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

from dynoscale.asgi import DynoscaleAsgiApp


async def home(_):
    return Response("Hello from Starlette, scaled by Dynoscale!", media_type='text/plain')


app = DynoscaleAsgiApp(Starlette(debug=True, routes=[Route('/', endpoint=home, methods=['GET'])]))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run('web:app', host='0.0.0.0', port=int(os.getenv('PORT', '8000')), log_level="info")

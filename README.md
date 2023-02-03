# Dynoscale Agent

### Simple yet efficient scaling agent for Python apps on Heroku

Dynoscale Agent supports both **WSGI** and **ASGI** based apps and **RQ** workers _(DjangoQ and Celery support is coming
soon)_.
The easies way to use it in your project is import the included Gunicorn hook in your _gunicorn.conf.py_ but we'll
explain
the setup process in more detail below.

### Note that for auto-scaling to work, your web/workers have to run on _Standard_ or _Performace_ dynos!

## Getting started

There are generally 3 steps to set up autoscaling with Dynoscale:

1) Add **Dynoscale** addon to your Heroku app
2) Install **dynoscale** package
3) Initialize **dynoscale** when you app starts

### 1) Enabling Dynoscale add-on

There are two ways to add the Dynoscale add-on to your app. Either you can add it through the broser from Heroku
dashboard by navigating to _your app_, then selecting the _resources_ tab and finally searching for _Dynoscale_ then
select your plan and at this point your app will be restarted.

### 2) Installing dynoscale agent package

This is same as installing any other Python package, for example: `python -m pip install dynoscale`.

If you'd like to confirm it's installed by heroku, then run:

    heroku run python -c "import dynoscale; print(dynoscale.__version__)"  

which will print out the installed version (for example: `1.1.3`)

If you'd like to confirm that dynoscale found the right env vars run:

    heroku run python -c "from dynoscale.config import Config; print(Config())"

and you'll likely see something like this:

    Running python -c "from dynoscale.config import Config; print(Config())" on ⬢ your-app-name-here... up, run.9816 (Eco)
    {"DYNO": "run.9816", "DYNOSCALE_DEV_MODE": false, "DYNOSCALE_URL": "https://dynoscale.net/api/v1/report/yoursecretdynoscalehash", "redis_urls": {"REDISCLOUD_URL": "redis://default:anothersecrethere@redis-12345.c258.us-east-1-4.ec2.cloud.redislabs.com:12345"}}

### 3) Initialize dynoscale during the app startup

This can take multiple forms and depends on your app. Is your app WSGI or ASGI? How do you serve it? Do you have
workers?

If you have a WSGI app _(ex.: Bottle, Flask, CherryPy, Pylons, Django, ...)_ and you serve the app with **Gunicorn**
then in your `gunicorn.conf.py` just import the pre_request hook from dynoscale and that's it:

```python
# `gunicorn.conf.py` - Using Dynoscale Gunicorn Hook
from dynoscale.hooks.gunicorn import pre_request  # noqa # pylint: disable=unused-import
```

Or if you prefer you can **instead** pass your WSGI app into DynoscaleWsgiApp():

```python
# `web.py` - Flask Example
from dynoscale.wsgi import DynoscaleWsgiApp

app = Flask(__name__)
app.wsgi_app = DynoscaleWsgiApp(app.wsgi_app)
```

If you have an ASGI app _(ex.: Starlette, Responder, FastAPI, Sanic, Django, Guillotina, ...)_ pass your ASGI app
into DynoscaleASGIApp:

```python
# `web.py` - Starlette Example
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
```

---

## 📖 More info on usage

1. Add __dynoscale__ to your app on Heroku: `heroku addons:create dscale`
2. Install __dynoscale__:  `python -m pip install dynoscale`
    1. Add __dynoscale__ to your app, you can either wrap your app or if you use Gunicorn, you can also just use one of
       its hooks (`pre_request`):
        1. If you want to wrap you app (let's look at Flask example):
       ```python
       import os
       
       from flask import Flask
    
       app = Flask(__name__)
       
       @app.route("/")
       def index():
           return "Hello from Flask!"
    
       if __name__ == "__main__":
           app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8000')), debug=True)
       ```
       then just wrap your WSGI app like this
       ```python
       from flask import Flask
       # FIRST, IMPORT DYNOSCALE
       from dynoscale.wsgi import DynoscaleWsgiApp
    
       app = Flask(__name__)
       
       @app.route("/")
       def index():
           return "Hello from Flask!"
       
       if __name__ == "__main__":
           # THE CHANGE BELOW IS ALL YOU NEED TO DO
           app.wsgi_app = DynoscaleWsgiApp(app.wsgi_app)
           # YUP, WE KNOW, CAN'T GET SIMPLER THAN THAT :)
           app.run(host='127.0.0.1', port=3000, debug=True)
       ```
    2. Or, if you'd prefer to use the hook, then change your `gunicorn.conf.py` accordingly instead:
       ```python
       # This one line will do it for you:
       from dynoscale.hooks.gunicorn import pre_request  # noqa # pylint: disable=unused-import
       ``` 
       If you already use the `pre_request` hook, alias ours and call it manually:
       ```python
       # Alias the import...
       from dynoscale.hooks.gunicorn import pre_request as hook
       
       # ...and remember to call ours first!
       def pre_request(worker, req):
          hook(worker, req)
          # ...do your own thing...
       ```
3. __Profit!__ _Literally, this will save you money! 💰💰💰 😏_

## ℹ️ Info

You should consider the `dynoscale.wsgi.DynoscaleWsgiApp(wsgi_app)`
and `dynoscale.hooks.gunicorn.pre_request(worker, req)` the only two bits of public interface.

## 🤯 Examples

Please check out `./examples`, yes, we do have examples in the repository :)

## 👩‍💻 Contributing

Install development requirements:
 - `pip install -e ".[test]"`

You can run _pytest_ from terminal: `pytest`

You can run _flake8_ from terminal: `flake8 ./src`  

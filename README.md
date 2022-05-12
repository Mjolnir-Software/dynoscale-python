# Dynoscale Agent

#### Simple yet efficient scaling agent for Python apps on Heroku

## 📖 Usage

1. Add __dynoscale__ to your app on Heroku: `heroku addons:create dscale`
2. Install __dynoscale__:  `python -m pip install dynoscale`
    1. Add __dynoscale__ to your app, you can either wrap your app or if you use Gunicorn, you can also just use one of
       its hooks (`pre_request`):
        1. If you want to wrap you app (let's look at Flask example):
       ```python
       from flask import Flask
    
       app = Flask(__name__)
       
       @app.route("/")
       def index():
           return "Hello from Flask!"
    
       if __name__ == "__main__":
           app.run(host='127.0.0.1', port=3000, debug=True)
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

Feel free to check out `./examples`, yes, we do have examples in the repository :)

## 👩‍💻 Contributing

Install development requirements by running `noglob pip install -e .[test]` if you use ZSH, or
`pip install -e .[test]` if you're stuck with Bash.

You can run _pytest_ from terminal: `pytest`

You can run _flake8_ from terminal: `flake8 ./src`  

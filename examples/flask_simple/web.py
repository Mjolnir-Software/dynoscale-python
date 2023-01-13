import os

from flask import Flask

from dynoscale.wsgi import DynoscaleWsgiApp

app = Flask(__name__)
app.wsgi_app = DynoscaleWsgiApp(app.wsgi_app)


@app.route("/")
def index():
    return "Hello from Flask, scaled by Dynoscale!"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8000')), debug=True)

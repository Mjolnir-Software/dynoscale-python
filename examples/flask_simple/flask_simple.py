import logging
import sys

import colorlog
from flask import Flask

from dynoscale.wsgi import DynoscaleWsgiApp

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

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


@app.route("/")
def index():
    app.logger.info('################### index requested')
    return "<h1 style='color:blue'>Hello from Flask!</h1>"


# THE LINE BELOW IS ALL YOU NEED TO USE DYNOSCALE
dynoscale_app = DynoscaleWsgiApp(app.wsgi_app)
# YUP, WE KNOW, CAN'T GET MUCH SIMPLER THAN THAT :)

if __name__ == "__main__":
    if 'wrap' in sys.argv:
        app.wsgi_app = dynoscale_app
    app.run(host='127.0.0.1', port=3000, debug=True)

import logging
import sys

import colorlog


# Configure logging
handler = colorlog.StreamHandler(stream=sys.stdout)
handler.setFormatter(
    colorlog.ColoredFormatter(
        fmt="%(asctime)s.%(msecs)03d %(log_color)s%(levelname)-8s %(processName)s %(threadName)10s%(reset)s"
            " %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
)


logging.getLogger("").handlers = [handler]
logging.getLogger("dynoscale").setLevel(logging.DEBUG)


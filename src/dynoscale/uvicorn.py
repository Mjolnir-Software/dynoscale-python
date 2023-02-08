import logging
from typing import Any

from uvicorn.workers import UvicornWorker
from dynoscale.asgi import DynoscaleAsgiApp


class DynoscaleUvicornWorker(UvicornWorker):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._dynoscale_logger: logging.Logger = logging.getLogger(f"{__name__}.{DynoscaleUvicornWorker.__name__}")
        self._dynoscale_logger.debug("__init__")
        super().__init__(*args, **kwargs)
        self._dynoscale_logger.info(f"{DynoscaleUvicornWorker.__name__} initialized.")

    def __repr__(self) -> str:
        return f"{DynoscaleUvicornWorker.__name__}({super().__repr__()})"

    def load_wsgi(self):
        self._dynoscale_logger.debug("load_wsgi()")
        self.app.callable = DynoscaleAsgiApp(self.app.callable)
        self._dynoscale_logger.info("App callable wrapped in DynoscaleAsgiApp.")
        super().load_wsgi()

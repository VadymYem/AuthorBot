import asyncio
import logging
from collections import OrderedDict
from threading import Thread

from werkzeug import Request, Response
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import BaseWSGIServer, make_server

from .. import main, utils

logger = logging.getLogger(__name__)


class ServerThread(Thread):
    def __init__(self, server: BaseWSGIServer):
        super().__init__(daemon=True)
        self.server = server

    def run(self):
        logger.debug("Starting local Werkzeug debug server")
        self.server.serve_forever()

    def shutdown(self):
        logger.debug("Shutting down local Werkzeug debug server")
        self.server.shutdown()


class WebDebugger:
    """Read-only local traceback viewer.

    It deliberately does not create a public reverse tunnel and does not enable
    Werkzeug's interactive eval console. This process holds Telegram sessions
    and must never expose arbitrary Python execution over the network.
    """

    def __init__(self):
        self.exceptions = OrderedDict()
        self.port = main.gen_port("werkzeug_port", True)
        main.save_config_key("werkzeug_port", self.port)
        self._create_server()
        self._controller = ServerThread(self._server)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        self._controller.start()
        utils.atexit(self._controller.shutdown)
        self.proxy_ready = asyncio.Event()
        self.proxy_ready.set()

    def _create_server(self) -> BaseWSGIServer:
        @Request.application
        def app(request):
            if request.args.get("ping", "N").upper() == "Y":
                return Response("ok")

            exception = self.exceptions.get(request.args.get("ex_id"))
            if exception is None:
                return Response("Traceback not found", status=404)

            raise exception

        # evalex=False is intentional: no remote/local browser may execute
        # arbitrary Python in the AuthorBot process.
        safe_app = DebuggedApplication(app, evalex=False, pin_security=True)
        self._server = make_server(
            "127.0.0.1",
            self.port,
            safe_app,
            threaded=False,
            processes=1,
            request_handler=None,
            passthrough_errors=False,
            ssl_context=None,
        )
        return self._server

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def feed(self, exc_type, exc_value, exc_traceback) -> str:
        logger.debug("Feeding exception %s to local debugger", exc_type)
        id_ = utils.rand(16)
        self.exceptions[id_] = exc_type(exc_value).with_traceback(exc_traceback)

        while len(self.exceptions) > 20:
            self.exceptions.popitem(last=False)

        return f"{self.url}/?ex_id={id_}"

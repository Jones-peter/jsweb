import logging

import uvicorn

from jsweb.logging_config import setup_logging
from jsweb.utils import get_local_ip

setup_logging()
logger = logging.getLogger(__name__)


def run(app, host="127.0.0.1", port=8000, reload=False):
    """
    Runs the ASGI application server using Uvicorn.

    This function starts the Uvicorn server to serve the given ASGI application.
    It logs the addresses the server is running on and handles the Uvicorn
    server lifecycle.

    Args:
        app: The ASGI application instance to run.
        host (str): The host address to bind the server to. Defaults to "127.0.0.1".
                    Use "0.0.0.0" to make the server accessible on the local network.
        port (int): The port number to listen on. Defaults to 8000.
        reload (bool): If True, enables auto-reloading for development. The server
                       will restart when code changes are detected. Defaults to False.
    """
    if host in ("0.0.0.0", "::"):
        local_ip = get_local_ip()
        logger.info("[*] JsWeb server running on:")
        logger.info(f"    > http://localhost:{port}")
        logger.info(f"    > http://{local_ip}:{port}  (LAN access)")
    else:
        logger.info(f"[*] JsWeb server running on http://{host}:{port}")
    logger.info("[*] Press Ctrl+C to stop the server")

    uvicorn.run(app, host=host, port=port, log_config=None, reload=reload)

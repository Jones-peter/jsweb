import logging
import uvicorn
from jsweb.logging_config import setup_logging
from jsweb.utils import get_local_ip

setup_logging()
logger = logging.getLogger(__name__)

def run(app, host="127.0.0.1", port=8000, reload=False):
    """
    Runs the ASGI application server using Uvicorn.
    """
    if host in ("0.0.0.0", "::"):
        local_ip = get_local_ip()
        logger.info("[*] JsWeb server running on:")
        logger.info(f"    > http://localhost:{port}")
        logger.info(f"    > http://{local_ip}:{port}  (LAN access)")
    else:
        logger.info(f"[*] JsWeb server running on http://{host}:{port}")
    logger.info("[*] Press Ctrl+C to stop the server")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=None,
        reload=reload
    )

import logging
import sys


def setup_logging():
    """
    Configures the logging for the application.

    This function sets up a basic configuration for logging, silences noisy
    third-party loggers, and customizes the format of Uvicorn's access logs
    to appear as if they are coming from 'jsweb.access'.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    access_logger = logging.getLogger("uvicorn.access")

    access_handler = logging.StreamHandler(sys.stdout)

    access_formatter = logging.Formatter(
        "%(asctime)s - jsweb.access - %(levelname)s - %(message)s"
    )

    access_handler.setFormatter(access_formatter)
    access_logger.handlers = [access_handler]

    access_logger.propagate = False

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


setup_logging()

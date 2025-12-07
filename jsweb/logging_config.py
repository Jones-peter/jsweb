import logging
import sys

def setup_logging():
    # General logging setup for jsweb and other libraries
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Silence Uvicorn's own startup/shutdown messages
    logging.getLogger('uvicorn.error').setLevel(logging.WARNING)

    # Intercept uvicorn's access logger to rebrand it
    access_logger = logging.getLogger('uvicorn.access')
    
    # Create a new handler for access logs
    access_handler = logging.StreamHandler(sys.stdout)
    
    # Create a new formatter that replaces 'uvicorn.access' with 'jsweb.access'
    access_formatter = logging.Formatter('%(asctime)s - jsweb.access - %(levelname)s - %(message)s')
    
    # Set the new formatter and replace the handlers
    access_handler.setFormatter(access_formatter)
    access_logger.handlers = [access_handler]
    
    # Stop the access logger from propagating to the root logger to avoid double logging
    access_logger.propagate = False

    # Set a higher level for other noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.INFO)


# Call setup_logging when this module is imported
setup_logging()

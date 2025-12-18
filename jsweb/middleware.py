import secrets
import logging
from .static import serve_static
from .response import Forbidden

logger = logging.getLogger(__name__)

class Middleware:
    """
    Base class for ASGI middleware.

    Args:
        app: The ASGI application to wrap.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        The ASGI application interface.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        await self.app(scope, receive, send)

class CSRFMiddleware(Middleware):
    """
    Middleware to protect against Cross-Site Request Forgery (CSRF) attacks.

    This middleware checks for a valid CSRF token in POST, PUT, PATCH, and DELETE
    requests. It supports both form-based and JSON-based requests.
    """

    async def __call__(self, scope, receive, send):
        """
        Validates the CSRF token for state-changing HTTP methods.

        If validation fails, it returns a 403 Forbidden response. Otherwise, it
        passes the request to the next application in the stack.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = scope['jsweb.request']

        if req.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = await self._get_token_from_request(req)
            cookie_token = req.cookies.get("csrf_token")

            if not token or not cookie_token or not secrets.compare_digest(token, cookie_token):
                logger.error("CSRF VALIDATION FAILED. Tokens do not match or are missing.")
                response = Forbidden("CSRF token missing or invalid.")
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    async def _get_token_from_request(self, req):
        """
        Extracts the CSRF token from the request, handling both JSON and form data.
        """
        content_type = req.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                data = await req.json()
                return data.get("csrf_token")
            except Exception:
                # In case of malformed JSON, treat as if no token was sent
                return None
        else:
            # Fallback for form data
            form = await req.form()
            return form.get("csrf_token")

class StaticFilesMiddleware(Middleware):
    """
    Middleware for serving static files.

    It intercepts requests that match the configured static URL paths for the main app
    and any registered blueprints, and serves the corresponding file if found.

    Args:
        app: The ASGI application to wrap.
        static_url (str): The URL prefix for the main application's static files.
        static_dir (str): The directory path for the main application's static files.
        blueprint_statics (list, optional): A list of blueprint static file configurations.
    """
    def __init__(self, app, static_url, static_dir, blueprint_statics=None):
        super().__init__(app)
        self.static_url = static_url
        self.static_dir = static_dir
        self.blueprint_statics = blueprint_statics or []

    async def __call__(self, scope, receive, send):
        """
        Handles requests for static files.

        It checks if the request path matches any of the static file URL prefixes.
        If a match is found, it attempts to serve the file. Otherwise, it passes
        the request to the next application.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = scope['jsweb.request']

        # Check blueprint static files first
        for bp in self.blueprint_statics:
            if bp.static_url_path and req.path.startswith(bp.static_url_path):
                response = serve_static(req.path, bp.static_url_path, bp.static_folder)
                await response(scope, receive, send)
                return

        # Fallback to main static files
        if req.path.startswith(self.static_url):
            response = serve_static(req.path, self.static_url, self.static_dir)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

class DBSessionMiddleware(Middleware):
    """
    Manages the lifecycle of a database session for each HTTP request.

    This middleware ensures that a SQLAlchemy session is properly handled. It commits
    the transaction if the request is successful, rolls it back upon an exception,
    and always removes the session at the end of the request.
    """
    async def __call__(self, scope, receive, send):
        """
        Wraps the request with a database session scope.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        from .database import db_session
        try:
            await self.app(scope, receive, send)
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.remove()

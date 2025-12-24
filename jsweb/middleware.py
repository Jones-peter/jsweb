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

    This middleware enforces CSRF protection for all state-changing HTTP methods
    (POST, PUT, PATCH, DELETE). It requires a valid CSRF token to be present
    in the request, either in the 'X-CSRF-Token' header or in the request body
    (JSON or Form Data).
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
            cookie_token = req.cookies.get("csrf_token")
            submitted_token = None

            
            submitted_token = req.headers.get("x-csrf-token")

        
            if not submitted_token:
                content_type = req.headers.get("content-type", "")

                if "application/json" in content_type:
                    try:
                        # Request.json() safely returns {} for empty/invalid bodies
                        data = await req.json()
                        submitted_token = data.get("csrf_token")
                    except Exception:
                        # If JSON parsing fails, we treat it as no token found
                        pass

                elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                    try:
                        # Request.form() safely returns {} for empty/non-form bodies
                        form = await req.form()
                        submitted_token = form.get("csrf_token")
                    except Exception:
                        # If form parsing fails, we treat it as no token found
                        pass

            
            # Both the cookie token and the submitted token MUST be present and match.
            if not cookie_token or not submitted_token or not secrets.compare_digest(submitted_token, cookie_token):
                # Log CSRF failure with context (but never log the actual tokens)
                client_ip = scope.get("client", ["unknown"])[0]
                logger.warning(
                    f"CSRF validation failed - Method: {req.method}, "
                    f"Path: {req.path}, Client IP: {client_ip}, "
                    f"Cookie set: {'Yes' if cookie_token else 'No'}, "
                    f"Token submitted: {'Yes' if submitted_token else 'No'}."
                )
                response = Forbidden("CSRF token missing or invalid.")
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

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
            status_code = None

            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                await send(message )

            await self.app(scope, receive, send_wrapper)

            # Commit only if the response status code is a success (2xx)
            # If status_code is None, it means no response was sent, which is an error state
            # or a successful response that didn't send headers yet (unlikely in a standard flow).
            # It's safer to rollback if status_code is not set or is not 2xx.
            if status_code is not None and 200 <= status_code < 300:
                db_session.commit()
            else:
                db_session.rollback()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.remove()


class SecurityHeadersMiddleware(Middleware):
    """
    Middleware to inject security headers into all HTTP responses.

    This middleware adds essential security headers to protect against common web
    vulnerabilities including XSS, clickjacking, MIME sniffing, and more.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: default-src 'self'

    Args:
        app: The ASGI application to wrap.
        custom_headers (dict, optional): Custom security headers to override defaults.
    """

    DEFAULT_HEADERS = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "x-xss-protection": "1; mode=block",
        "strict-transport-security": "max-age=31536000; includeSubDomains",
        "referrer-policy": "strict-origin-when-cross-origin",
        # Conservative CSP - can be customized per-application
        "content-security-policy": "default-src 'self'",
    }

    def __init__(self, app, custom_headers=None):
        super().__init__(app)
        self.headers = {**self.DEFAULT_HEADERS, **(custom_headers or {})}

    async def __call__(self, scope, receive, send):
        """
        Injects security headers into the HTTP response.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add security headers to response
                headers = list(message.get("headers", []))

                # Only add headers if they don't already exist
                existing_header_names = {name.decode().lower() for name, _ in headers}

                for header_name, header_value in self.headers.items():
                    if header_name.lower() not in existing_header_names:
                        headers.append([header_name.encode(), header_value.encode()])

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_wrapper)

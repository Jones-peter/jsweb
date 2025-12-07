import secrets
import logging
from .static import serve_static
from .response import Forbidden

logger = logging.getLogger(__name__)

class Middleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)

class CSRFMiddleware(Middleware):
    """Middleware to protect against Cross-Site Request Forgery attacks."""
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = scope['jsweb.request']

        if req.method in ("POST", "PUT", "PATCH", "DELETE"):
            form = await req.form()
            form_token = form.get("csrf_token")
            cookie_token = req.cookies.get("csrf_token")

            if not form_token or not cookie_token or not secrets.compare_digest(form_token, cookie_token):
                logger.error("CSRF VALIDATION FAILED. Tokens do not match or are missing.")
                response = Forbidden("CSRF token missing or invalid.")
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

class StaticFilesMiddleware(Middleware):
    def __init__(self, app, static_url, static_dir, blueprint_statics=None):
        super().__init__(app)
        self.static_url = static_url
        self.static_dir = static_dir
        self.blueprint_statics = blueprint_statics or []

    async def __call__(self, scope, receive, send):
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
    async def __call__(self, scope, receive, send):
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

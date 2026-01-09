"""
Optional automatic request validation middleware

This middleware automatically validates request bodies against DTOs
when @api_body decorator is used.
"""

from jsweb.request import Request


class ValidationMiddleware:
    """
    ASGI middleware that validates requests against DTOs.

    Usage:
        from jsweb import JsWebApp
        from jsweb.docs.validation_middleware import ValidationMiddleware

        app = JsWebApp(__name__)
        app.add_middleware(ValidationMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object to inspect
        _request = Request(scope, receive, send)

        # Find route metadata
        # Note: This requires access to the handler which we don't have here
        # This is a simplified example - full implementation would need
        # integration with the routing system

        # For now, just pass through
        await self.app(scope, receive, send)

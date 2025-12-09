"""
Easy setup for OpenAPI documentation in jsweb apps

This module provides one-line setup functions for enabling
automatic API documentation with Swagger UI and ReDoc.
"""

from typing import Dict, List, Any, Optional
from .schema_builder import OpenAPISchemaBuilder
from .ui_handlers import (
    set_builder,
    openapi_json_handler,
    swagger_ui_handler,
    redoc_handler,
    rapidoc_handler
)
from .introspection import introspect_app_routes
from .registry import openapi_registry


def configure_openapi(
    title: str = "Jsweb API",
    version: str = "1.0.0",
    description: str = "",
    terms_of_service: str = None,
    contact: Dict[str, str] = None,
    license_info: Dict[str, str] = None,
    servers: List[Dict[str, str]] = None,
    tags: List[Dict[str, Any]] = None
) -> OpenAPISchemaBuilder:
    """
    Configure OpenAPI documentation settings.

    Args:
        title: API title
        version: API version
        description: API description (supports markdown)
        terms_of_service: URL to terms of service
        contact: Contact info {'name': '...', 'email': '...', 'url': '...'}
        license_info: License info {'name': '...', 'url': '...'}
        servers: List of servers [{'url': '...', 'description': '...'}]
        tags: List of tags [{'name': '...', 'description': '...'}]

    Returns:
        Configured OpenAPISchemaBuilder instance

    Example:
        builder = configure_openapi(
            title="My API",
            version="2.0.0",
            description="My awesome API built with jsweb",
            contact={
                "name": "API Support",
                "email": "support@example.com",
                "url": "https://example.com/support"
            },
            license_info={
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            },
            tags=[
                {"name": "Users", "description": "User management endpoints"},
                {"name": "Admin", "description": "Admin operations"}
            ]
        )
    """
    builder = OpenAPISchemaBuilder(
        title=title,
        version=version,
        description=description,
        terms_of_service=terms_of_service,
        contact=contact,
        license_info=license_info,
        servers=servers,
        tags=tags
    )

    set_builder(builder)
    return builder


def setup_openapi_docs(
    app,
    *,
    title: str = "jsweb API",
    version: str = "1.0.0",
    description: str = "",
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
    rapidoc_url: str = None,
    openapi_url: str = "/openapi.json",
    security_schemes: Dict[str, Dict] = None,
    **kwargs
):
    """
    One-line setup for OpenAPI documentation.

    This function must be called AFTER all blueprints are registered.

    Args:
        app: JsWebApp instance
        title: API title
        version: API version
        description: API description
        docs_url: URL for Swagger UI (None to disable)
        redoc_url: URL for ReDoc UI (None to disable)
        rapidoc_url: URL for RapiDoc UI (None to disable)
        openapi_url: URL for OpenAPI JSON spec (None to disable)
        security_schemes: Security schemes dict
        **kwargs: Additional OpenAPI configuration

    Example:
        from jsweb import JsWebApp
        from jsweb.docs import setup_openapi_docs

        app = JsWebApp(__name__)

        # Register blueprints
        app.register_blueprint(api_bp)
        app.register_blueprint(admin_bp)

        # Setup docs (MUST be after blueprint registration!)
        setup_openapi_docs(
            app,
            title="My API",
            version="1.0.0",
            description="My awesome API built with jsweb",
            security_schemes={
                "bearer_auth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        )

        if __name__ == "__main__":
            app.run(port=8000)
    """
    # Configure OpenAPI schema builder
    configure_openapi(
        title=title,
        version=version,
        description=description,
        **kwargs
    )

    # Register security schemes if provided
    if security_schemes:
        for name, scheme in security_schemes.items():
            openapi_registry.add_security_scheme(name, scheme)

    # Introspect routes and complete metadata
    introspect_app_routes(app)

    # Register documentation routes
    if openapi_url:
        app.route(openapi_url, methods=["GET"])(openapi_json_handler)

    if docs_url:
        app.route(docs_url, methods=["GET"])(swagger_ui_handler)

    if redoc_url:
        app.route(redoc_url, methods=["GET"])(redoc_handler)

    if rapidoc_url:
        app.route(rapidoc_url, methods=["GET"])(rapidoc_handler)

    # Print documentation URLs (ASCII-safe for Windows terminals)
    print(f"\n[*] OpenAPI documentation enabled:")
    if docs_url:
        print(f"   > Swagger UI: {docs_url}")
    if redoc_url:
        print(f"   > ReDoc:      {redoc_url}")
    if rapidoc_url:
        print(f"   > RapiDoc:    {rapidoc_url}")
    if openapi_url:
        print(f"   > JSON spec:  {openapi_url}")
    print()


def add_security_scheme(
    name: str,
    *,
    type: str,
    scheme: str = None,
    bearer_format: str = None,
    flows: Dict = None,
    **kwargs
):
    """
    Add a security scheme to the OpenAPI spec.

    Args:
        name: Security scheme name (referenced in @api_security)
        type: Type ('apiKey', 'http', 'oauth2', 'openIdConnect')
        scheme: Scheme for http type ('basic', 'bearer')
        bearer_format: Bearer token format (e.g., 'JWT')
        flows: OAuth2 flows configuration
        **kwargs: Additional security scheme properties

    Examples:
        # JWT Bearer token
        add_security_scheme(
            "bearer_auth",
            type="http",
            scheme="bearer",
            bearer_format="JWT"
        )

        # API Key in header
        add_security_scheme(
            "api_key",
            type="apiKey",
            in_="header",
            name="X-API-Key"
        )

        # OAuth2
        add_security_scheme(
            "oauth2",
            type="oauth2",
            flows={
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/oauth/authorize",
                    "tokenUrl": "https://example.com/oauth/token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access"
                    }
                }
            }
        )
    """
    security_scheme = {
        "type": type,
        **kwargs
    }

    if scheme:
        security_scheme["scheme"] = scheme
    if bearer_format:
        security_scheme["bearerFormat"] = bearer_format
    if flows:
        security_scheme["flows"] = flows

    openapi_registry.add_security_scheme(name, security_scheme)

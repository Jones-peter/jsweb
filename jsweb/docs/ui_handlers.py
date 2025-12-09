"""
UI handlers for Swagger UI and ReDoc

Serves documentation interfaces and OpenAPI JSON spec.
"""

import json as json_module
from .schema_builder import OpenAPISchemaBuilder

# Global builder instance (configured by user)
_builder: OpenAPISchemaBuilder = None


def set_builder(builder: OpenAPISchemaBuilder):
    """Set the global schema builder instance."""
    global _builder
    _builder = builder


def get_builder() -> OpenAPISchemaBuilder:
    """Get the global schema builder instance."""
    global _builder
    if _builder is None:
        # Create default builder if not configured
        _builder = OpenAPISchemaBuilder()
    return _builder


async def openapi_json_handler(req):
    """
    Serve OpenAPI JSON spec at /openapi.json

    This endpoint provides the raw OpenAPI specification that can be
    used by tools like Postman, Insomnia, or code generators.
    """
    builder = get_builder()
    spec = builder.build()

    # Import jsweb's json response
    try:
        from jsweb.response import JSONResponse
        return JSONResponse(spec)
    except ImportError:
        # Fallback for testing
        return {
            'status': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json_module.dumps(spec)
        }


async def swagger_ui_handler(req):
    """
    Serve Swagger UI at /docs

    Swagger UI is the most popular OpenAPI documentation interface.
    It provides:
    - Interactive API documentation
    - Try-it-out functionality
    - Request/response examples
    - Schema validation
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui.css">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
        .topbar {
            display: none;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                persistAuthorization: true,
                displayRequestDuration: true,
                filter: true,
                tryItOutEnabled: true
            });
        };
    </script>
</body>
</html>"""

    # Import jsweb's HTML response
    try:
        from jsweb.response import HTMLResponse
        return HTMLResponse(html)
    except ImportError:
        # Fallback for testing
        return {
            'status': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html
        }


async def redoc_handler(req):
    """
    Serve ReDoc UI at /redoc

    ReDoc is a clean, responsive documentation interface.
    It provides:
    - Beautiful three-panel layout
    - Search functionality
    - Code samples in multiple languages
    - Better for large APIs with many endpoints
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - ReDoc</title>
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <redoc
        spec-url='/openapi.json'
        hide-hostname="true"
        expand-responses="200,201"
        path-in-middle-panel="true"
        native-scrollbars="true"
    ></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""

    # Import jsweb's HTML response
    try:
        from jsweb.response import HTMLResponse
        return HTMLResponse(html)
    except ImportError:
        # Fallback for testing
        return {
            'status': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html
        }


async def rapidoc_handler(req):
    """
    Serve RapiDoc UI at /rapidoc (alternative UI)

    RapiDoc is a modern alternative with customizable themes.
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - RapiDoc</title>
    <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
</head>
<body>
    <rapi-doc
        spec-url="/openapi.json"
        theme="dark"
        show-header="false"
        allow-try="true"
        allow-server-selection="false"
        allow-authentication="true"
        render-style="view"
        schema-style="table"
        default-schema-tab="model"
    ></rapi-doc>
</body>
</html>"""

    try:
        from jsweb.response import HTMLResponse
        return HTMLResponse(html)
    except ImportError:
        return {
            'status': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': html
        }

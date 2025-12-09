"""
Route introspection - Automatically extract metadata from jsweb routes

This module introspects the jsweb app's routes and automatically:
- Detects path parameters
- Extracts docstrings
- Completes partial metadata
- Registers schemas from DTOs
"""

import re
import inspect
from typing import Any, Dict
from .registry import openapi_registry, RouteMetadata, ParameterMetadata


def introspect_app_routes(app):
    """
    Introspect routes from JsWebApp instance.

    This function should be called after all blueprints are registered.
    It automatically completes metadata for routes that have been
    decorated with OpenAPI decorators.

    Args:
        app: JsWebApp instance

    Example:
        app = JsWebApp(__name__)
        app.register_blueprint(api_bp)

        # After all blueprints are registered
        introspect_app_routes(app)
    """
    router = app.router

    # Iterate through all registered routes
    for endpoint, route in router.endpoints.items():
        handler = route.handler
        path = route.path
        methods = route.methods or ["GET"]

        # Get or create metadata for this handler
        metadata = openapi_registry.get_or_create_route(handler)

        # Complete metadata from route info
        metadata.path = path
        metadata.method = methods[0]  # Primary method
        metadata.endpoint = endpoint

        # If no summary/description, try to extract from docstring
        if not metadata.summary and handler.__doc__:
            metadata.summary = _extract_summary_from_docstring(handler)
        if not metadata.description and handler.__doc__:
            metadata.description = handler.__doc__.strip()

        # Auto-detect path parameters
        _add_path_parameters(metadata, path)

        # Register any DTO schemas used in this route
        _register_dto_schemas(metadata)


def _extract_summary_from_docstring(handler) -> str:
    """
    Extract first line of docstring as summary.

    Args:
        handler: Route handler function

    Returns:
        First line of docstring or empty string
    """
    if handler.__doc__:
        lines = handler.__doc__.strip().split('\n')
        return lines[0].strip() if lines else ""
    return ""


def _add_path_parameters(metadata: RouteMetadata, path: str):
    """
    Extract path parameters from jsweb route path.

    Examples:
        /users/<int:user_id> -> parameter 'user_id' with type integer
        /files/<path:filepath> -> parameter 'filepath' with type string
        /posts/<id> -> parameter 'id' with type string

    Args:
        metadata: Route metadata to update
        path: jsweb route path
    """
    # Pattern matches: <int:id>, <str:name>, <path:filepath>, <id>
    pattern = r'<(?:(\w+):)?(\w+)>'
    matches = re.finditer(pattern, path)

    for match in matches:
        param_type = match.group(1) or 'str'
        param_name = match.group(2)

        # Check if already documented (user may have added explicitly)
        if any(p.name == param_name and p.location == 'path' for p in metadata.parameters):
            continue

        # Map jsweb types to OpenAPI types
        type_map = {
            'int': {'type': 'integer', 'format': 'int32'},
            'str': {'type': 'string'},
            'path': {'type': 'string'},
            'float': {'type': 'number', 'format': 'float'},
        }

        schema = type_map.get(param_type, {'type': 'string'})

        param = ParameterMetadata(
            name=param_name,
            location='path',
            schema=schema,
            required=True,  # Path parameters are always required
            description=f"Path parameter: {param_name}"
        )

        metadata.parameters.append(param)


def _register_dto_schemas(metadata: RouteMetadata):
    """
    Register DTO schemas from route metadata.

    Extracts DTO classes from request body and responses,
    then registers their OpenAPI schemas in the components section.

    Args:
        metadata: Route metadata
    """
    # Register request body DTO
    if metadata.request_body and metadata.request_body.dto_class:
        dto_class = metadata.request_body.dto_class
        _register_dto_schema(dto_class)

    # Register response DTOs
    for response in metadata.responses.values():
        if response.dto_class:
            _register_dto_schema(response.dto_class)


def _register_dto_schema(dto_class):
    """
    Register a single DTO schema in the registry.

    Args:
        dto_class: DTO class (JswebBaseModel subclass)
    """
    if not hasattr(dto_class, 'openapi_schema'):
        return

    # Get model name for schema reference
    if hasattr(dto_class, 'get_model_name'):
        schema_name = dto_class.get_model_name()
    else:
        schema_name = dto_class.__name__

    # Check if already registered
    if openapi_registry.get_schema(schema_name):
        return

    # Get schema and register
    schema = dto_class.openapi_schema()
    openapi_registry.register_schema(schema_name, schema)

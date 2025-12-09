"""
NestJS-style decorators for API documentation

These decorators allow developers to add rich OpenAPI documentation to their routes.
"""

from functools import wraps
from typing import Type, Dict, Any, List, Optional, Union
from .registry import (
    openapi_registry,
    RouteMetadata,
    ResponseMetadata,
    RequestBodyMetadata,
    ParameterMetadata
)


def api_operation(
    summary: str = None,
    description: str = None,
    operation_id: str = None,
    deprecated: bool = False,
):
    """
    Document an API operation (NestJS-style).

    This decorator should be placed closest to the route decorator.

    Args:
        summary: Short summary of the operation
        description: Detailed description (uses docstring if not provided)
        operation_id: Unique operation ID (uses endpoint if not provided)
        deprecated: Mark operation as deprecated

    Example:
        @api_bp.route("/users", methods=["GET"])
        @api_operation(
            summary="List all users",
            description="Returns a paginated list of users with optional filtering",
            deprecated=False
        )
        async def list_users(req):
            '''Get all users in the system.'''
            return json({"users": [...]})
    """
    def decorator(handler):
        metadata = openapi_registry.get_or_create_route(handler)

        # Set operation details
        metadata.summary = summary or handler.__doc__
        metadata.description = description or handler.__doc__
        metadata.operation_id = operation_id
        metadata.deprecated = deprecated

        return handler
    return decorator


def api_response(
    status_code: int,
    dto: Type = None,
    description: str = "",
    content_type: str = "application/json",
    examples: Dict[str, Any] = None,
    headers: Dict[str, Dict] = None
):
    """
    Document an API response (NestJS-style).

    Args:
        status_code: HTTP status code (200, 404, etc.)
        dto: Response DTO class (JswebBaseModel subclass)
        description: Response description
        content_type: MIME type
        examples: Example responses
        headers: Response headers

    Example:
        @api_response(200, UserDto, description="User found")
        @api_response(404, ErrorDto, description="User not found")
        @api_response(400, ErrorDto, description="Invalid request")
        async def get_user(req, user_id):
            return json({"user": {...}})
    """
    def decorator(handler):
        metadata = openapi_registry.get_or_create_route(handler)

        # Build response content
        content = None
        if dto:
            # Check if DTO has OpenAPI schema method (from JswebBaseModel)
            if hasattr(dto, 'openapi_schema'):
                schema = dto.openapi_schema()
            else:
                # Fallback to basic object type
                schema = {"type": "object"}

            content = {
                content_type: {
                    "schema": schema
                }
            }

            if examples:
                content[content_type]["examples"] = examples

        response = ResponseMetadata(
            status_code=status_code,
            description=description,
            content=content,
            headers=headers,
            dto_class=dto  # Store for automatic serialization
        )

        metadata.responses[status_code] = response
        return handler
    return decorator


def api_body(
    dto: Type,
    description: str = "",
    content_type: str = "application/json",
    required: bool = True,
    examples: Dict[str, Any] = None
):
    """
    Document request body (NestJS-style).

    The DTO class will be used for:
    1. OpenAPI schema generation
    2. Automatic request validation (via middleware)

    Args:
        dto: Request body DTO class (JswebBaseModel subclass)
        description: Body description
        content_type: MIME type
        required: Whether body is required
        examples: Example request bodies

    Example:
        @api_bp.route("/users", methods=["POST"])
        @api_body(CreateUserDto, description="User data to create")
        @api_response(201, UserDto, description="User created")
        async def create_user(req):
            # req.validated_body will contain the validated DTO instance
            data = await req.json()
            return json({"user": {...}}, status=201)
    """
    def decorator(handler):
        metadata = openapi_registry.get_or_create_route(handler)

        # Get schema from DTO
        if hasattr(dto, 'openapi_schema'):
            schema = dto.openapi_schema()
        else:
            schema = {"type": "object"}

        # Add examples to schema if provided
        if examples:
            schema['examples'] = examples

        metadata.request_body = RequestBodyMetadata(
            content_type=content_type,
            schema=schema,
            description=description,
            required=required,
            dto_class=dto  # Store for automatic validation
        )

        # Mark handler with validation info (for middleware)
        if not hasattr(handler, '_jsweb_validation'):
            handler._jsweb_validation = {}
        handler._jsweb_validation['body_dto'] = dto

        return handler
    return decorator


def api_query(
    name: str,
    *,
    type: Type = str,
    required: bool = False,
    description: str = "",
    example: Any = None,
    deprecated: bool = False,
    **schema_kwargs
):
    """
    Document a query parameter (NestJS-style).

    Args:
        name: Parameter name
        type: Python type (str, int, float, bool, list)
        required: Whether parameter is required
        description: Parameter description
        example: Example value
        deprecated: Mark as deprecated
        **schema_kwargs: Additional OpenAPI schema properties

    Example:
        @api_query('page', type=int, required=False, description="Page number", example=1)
        @api_query('limit', type=int, required=False, description="Items per page", example=10)
        @api_query('search', type=str, required=False, description="Search query")
        async def list_users(req):
            page = int(req.query_params.get('page', 1))
            return json({"users": [...]})
    """
    def decorator(handler):
        metadata = openapi_registry.get_or_create_route(handler)

        # Convert Python type to OpenAPI schema
        schema = _type_to_schema(type, **schema_kwargs)
        if example is not None:
            schema['example'] = example

        param = ParameterMetadata(
            name=name,
            location='query',
            schema=schema,
            required=required,
            description=description,
            deprecated=deprecated,
            example=example
        )

        metadata.parameters.append(param)
        return handler
    return decorator


def api_header(
    name: str,
    *,
    type: Type = str,
    required: bool = False,
    description: str = "",
    example: Any = None,
    deprecated: bool = False,
    **schema_kwargs
):
    """
    Document a header parameter (NestJS-style).

    Args:
        name: Header name (e.g., 'Authorization', 'X-API-Key')
        type: Python type
        required: Whether header is required
        description: Header description
        example: Example value
        deprecated: Mark as deprecated
        **schema_kwargs: Additional OpenAPI schema properties

    Example:
        @api_header('X-API-Key', required=True, description="API key for authentication")
        @api_header('X-Request-ID', required=False, description="Request tracking ID")
        async def protected_route(req):
            api_key = req.headers.get('X-API-Key')
            return json({"data": "..."})
    """
    def decorator(handler):
        metadata = openapi_registry.get_or_create_route(handler)

        schema = _type_to_schema(type, **schema_kwargs)
        if example is not None:
            schema['example'] = example

        param = ParameterMetadata(
            name=name,
            location='header',
            schema=schema,
            required=required,
            description=description,
            deprecated=deprecated,
            example=example
        )

        metadata.parameters.append(param)
        return handler
    return decorator


def api_security(*schemes: str, scopes: List[str] = None):
    """
    Apply security requirements to an operation (NestJS-style).

    Args:
        *schemes: Security scheme names (must be registered)
        scopes: Required OAuth2 scopes (if applicable)

    Example:
        # First, register security schemes in setup_openapi_docs()
        openapi_registry.add_security_scheme("bearer_auth", {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        })

        # Then use in routes
        @api_security("bearer_auth")
        @api_response(200, UserDto)
        async def get_current_user(req):
            return json({"user": {...}})

        # OAuth2 with scopes
        @api_security("oauth2", scopes=["read:users", "write:users"])
        async def admin_route(req):
            return json({"data": "..."})
    """
    def decorator(handler):
        metadata = openapi_registry.get_or_create_route(handler)

        for scheme in schemes:
            metadata.security.append({scheme: scopes or []})

        return handler
    return decorator


def api_tags(*tags: str):
    """
    Add tags to an operation for grouping in documentation (NestJS-style).

    Args:
        *tags: Tag names

    Example:
        @api_tags("Users", "Admin")
        @api_operation(summary="Delete user")
        async def delete_user(req, user_id):
            return json({"message": "User deleted"})
    """
    def decorator(handler):
        metadata = openapi_registry.get_or_create_route(handler)
        metadata.tags.extend(tags)
        return handler
    return decorator


def _type_to_schema(py_type: Type, **kwargs) -> Dict[str, Any]:
    """
    Convert Python type to OpenAPI schema.

    Args:
        py_type: Python type (str, int, float, bool, list, etc.)
        **kwargs: Additional schema properties

    Returns:
        OpenAPI schema dictionary
    """
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array", "items": {"type": "string"}},
        dict: {"type": "object"},
    }

    schema = type_map.get(py_type, {"type": "string"}).copy()
    schema.update(kwargs)
    return schema

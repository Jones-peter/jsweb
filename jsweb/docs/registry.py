"""
OpenAPI metadata registry - Central storage for all route documentation
"""

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from threading import RLock
from typing import Any


@dataclass
class ParameterMetadata:
    """OpenAPI parameter definition."""

    name: str
    location: str  # 'path', 'query', 'header', 'cookie'
    schema: dict[str, Any]
    required: bool = True
    description: str = ""
    deprecated: bool = False
    example: Any = None


@dataclass
class RequestBodyMetadata:
    """OpenAPI request body definition."""

    content_type: str  # 'application/json', 'multipart/form-data', etc.
    schema: dict[str, Any]
    description: str = ""
    required: bool = True
    dto_class: type | None = None  # Store DTO class for validation


@dataclass
class ResponseMetadata:
    """OpenAPI response definition."""

    status_code: int
    description: str
    content: dict[str, dict] | None = None  # {'application/json': {'schema': {...}}}
    headers: dict[str, dict] | None = None
    dto_class: type | None = None  # Store DTO class for serialization


@dataclass
class RouteMetadata:
    """Complete OpenAPI operation metadata."""

    # Route identification
    handler: Callable
    path: str = ""
    method: str = ""
    endpoint: str = ""

    # OpenAPI operation fields
    summary: str | None = None
    description: str | None = None
    tags: list[str] = dataclass_field(default_factory=list)
    operation_id: str | None = None
    deprecated: bool = False

    # Parameters and body
    parameters: list[ParameterMetadata] = dataclass_field(default_factory=list)
    request_body: RequestBodyMetadata | None = None

    # Responses
    responses: dict[int, ResponseMetadata] = dataclass_field(default_factory=dict)

    # Security
    security: list[dict[str, list[str]]] = dataclass_field(default_factory=list)


class OpenAPIRegistry:
    """
    Thread-safe global registry for OpenAPI metadata.

    Stores all route documentation, schemas, and security definitions.
    """

    def __init__(self):
        self._routes: dict[Callable, RouteMetadata] = {}
        self._schemas: dict[str, dict] = {}
        self._security_schemes: dict[str, dict] = {}
        self._lock = RLock()

    def register_route(self, handler: Callable, metadata: RouteMetadata = None):
        """Register or update route metadata."""
        with self._lock:
            if metadata is None:
                # Create new metadata if doesn't exist
                if handler not in self._routes:
                    metadata = RouteMetadata(handler=handler)
                    self._routes[handler] = metadata
            else:
                self._routes[handler] = metadata

    def get_route(self, handler: Callable) -> RouteMetadata | None:
        """Get metadata for a route handler."""
        return self._routes.get(handler)

    def get_or_create_route(self, handler: Callable) -> RouteMetadata:
        """Get existing metadata or create new one."""
        with self._lock:
            if handler not in self._routes:
                metadata = RouteMetadata(handler=handler)
                self._routes[handler] = metadata
            return self._routes[handler]

    def all_routes(self) -> dict[Callable, RouteMetadata]:
        """Get all registered routes."""
        return self._routes.copy()

    def register_schema(self, name: str, schema: dict[str, Any]):
        """Register a reusable schema component."""
        with self._lock:
            self._schemas[name] = schema

    def get_schema(self, name: str) -> dict[str, Any] | None:
        """Get a registered schema by name."""
        return self._schemas.get(name)

    def all_schemas(self) -> dict[str, dict]:
        """Get all registered schemas."""
        return self._schemas.copy()

    def add_security_scheme(self, name: str, scheme: dict[str, Any]):
        """Register a security scheme (Bearer, OAuth2, etc.)."""
        with self._lock:
            self._security_schemes[name] = scheme

    def get_security_scheme(self, name: str) -> dict[str, Any] | None:
        """Get a security scheme by name."""
        return self._security_schemes.get(name)

    def all_security_schemes(self) -> dict[str, dict]:
        """Get all registered security schemes."""
        return self._security_schemes.copy()

    def clear(self):
        """Clear all registered data (useful for testing)."""
        with self._lock:
            self._routes.clear()
            self._schemas.clear()
            self._security_schemes.clear()


# Global registry instance
openapi_registry = OpenAPIRegistry()

"""
OpenAPI metadata registry - Central storage for all route documentation
"""

from typing import Dict, List, Optional, Callable, Any, Type
from dataclasses import dataclass, field as dataclass_field
from threading import RLock


@dataclass
class ParameterMetadata:
    """OpenAPI parameter definition."""
    name: str
    location: str  # 'path', 'query', 'header', 'cookie'
    schema: Dict[str, Any]
    required: bool = True
    description: str = ""
    deprecated: bool = False
    example: Any = None


@dataclass
class RequestBodyMetadata:
    """OpenAPI request body definition."""
    content_type: str  # 'application/json', 'multipart/form-data', etc.
    schema: Dict[str, Any]
    description: str = ""
    required: bool = True
    dto_class: Optional[Type] = None  # Store DTO class for validation


@dataclass
class ResponseMetadata:
    """OpenAPI response definition."""
    status_code: int
    description: str
    content: Optional[Dict[str, Dict]] = None  # {'application/json': {'schema': {...}}}
    headers: Optional[Dict[str, Dict]] = None
    dto_class: Optional[Type] = None  # Store DTO class for serialization


@dataclass
class RouteMetadata:
    """Complete OpenAPI operation metadata."""
    # Route identification
    handler: Callable
    path: str = ""
    method: str = ""
    endpoint: str = ""

    # OpenAPI operation fields
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = dataclass_field(default_factory=list)
    operation_id: Optional[str] = None
    deprecated: bool = False

    # Parameters and body
    parameters: List[ParameterMetadata] = dataclass_field(default_factory=list)
    request_body: Optional[RequestBodyMetadata] = None

    # Responses
    responses: Dict[int, ResponseMetadata] = dataclass_field(default_factory=dict)

    # Security
    security: List[Dict[str, List[str]]] = dataclass_field(default_factory=list)


class OpenAPIRegistry:
    """
    Thread-safe global registry for OpenAPI metadata.

    Stores all route documentation, schemas, and security definitions.
    """

    def __init__(self):
        self._routes: Dict[Callable, RouteMetadata] = {}
        self._schemas: Dict[str, Dict] = {}
        self._security_schemes: Dict[str, Dict] = {}
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

    def get_route(self, handler: Callable) -> Optional[RouteMetadata]:
        """Get metadata for a route handler."""
        return self._routes.get(handler)

    def get_or_create_route(self, handler: Callable) -> RouteMetadata:
        """Get existing metadata or create new one."""
        with self._lock:
            if handler not in self._routes:
                metadata = RouteMetadata(handler=handler)
                self._routes[handler] = metadata
            return self._routes[handler]

    def all_routes(self) -> Dict[Callable, RouteMetadata]:
        """Get all registered routes."""
        return self._routes.copy()

    def register_schema(self, name: str, schema: Dict[str, Any]):
        """Register a reusable schema component."""
        with self._lock:
            self._schemas[name] = schema

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered schema by name."""
        return self._schemas.get(name)

    def all_schemas(self) -> Dict[str, Dict]:
        """Get all registered schemas."""
        return self._schemas.copy()

    def add_security_scheme(self, name: str, scheme: Dict[str, Any]):
        """Register a security scheme (Bearer, OAuth2, etc.)."""
        with self._lock:
            self._security_schemes[name] = scheme

    def get_security_scheme(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a security scheme by name."""
        return self._security_schemes.get(name)

    def all_security_schemes(self) -> Dict[str, Dict]:
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

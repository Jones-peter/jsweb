"""
OpenAPI 3.0 schema builder

Generates complete OpenAPI specification from registry metadata.
"""

import re
from typing import Dict, Any, List, Optional
from .registry import openapi_registry, RouteMetadata


class OpenAPISchemaBuilder:
    """
    Builds OpenAPI 3.0 specification from registry metadata.

    Converts route metadata, DTOs, and security schemes into a complete
    OpenAPI spec that can be served as JSON or used with Swagger/ReDoc.
    """

    def __init__(
        self,
        title: str = "jsweb API",
        version: str = "1.0.0",
        description: str = "",
        terms_of_service: str = None,
        contact: Dict[str, str] = None,
        license_info: Dict[str, str] = None,
        servers: List[Dict[str, str]] = None,
        tags: List[Dict[str, Any]] = None
    ):
        """
        Initialize schema builder.

        Args:
            title: API title
            version: API version
            description: API description
            terms_of_service: URL to terms of service
            contact: Contact info {'name': '...', 'email': '...', 'url': '...'}
            license_info: License info {'name': '...', 'url': '...'}
            servers: List of servers [{'url': '...', 'description': '...'}]
            tags: List of tags for grouping [{'name': '...', 'description': '...'}]
        """
        self.title = title
        self.version = version
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.servers = servers or [{"url": "/", "description": "Current server"}]
        self.tags = tags or []

    def build(self) -> Dict[str, Any]:
        """
        Generate complete OpenAPI 3.0 specification.

        Returns:
            OpenAPI spec as dictionary
        """
        spec = {
            "openapi": "3.0.3",
            "info": self._build_info(),
            "servers": self.servers,
            "paths": self._build_paths(),
            "components": self._build_components()
        }

        if self.tags:
            spec["tags"] = self.tags

        return spec

    def _build_info(self) -> Dict[str, Any]:
        """Build info object."""
        info = {
            "title": self.title,
            "version": self.version,
        }

        if self.description:
            info["description"] = self.description
        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service
        if self.contact:
            info["contact"] = self.contact
        if self.license_info:
            info["license"] = self.license_info

        return info

    def _build_paths(self) -> Dict[str, Any]:
        """Build paths object from registered routes."""
        paths = {}

        for handler, metadata in openapi_registry.all_routes().items():
            if not metadata.path:
                # Skip routes without path (not yet introspected)
                continue

            # Convert jsweb path format to OpenAPI
            # /users/<int:id> -> /users/{id}
            # /files/<path:filepath> -> /files/{filepath}
            openapi_path = self._convert_path_format(metadata.path)

            if openapi_path not in paths:
                paths[openapi_path] = {}

            # Build operation object
            operation = self._build_operation(metadata)

            # Add operation to path
            method = metadata.method.lower()
            paths[openapi_path][method] = operation

        return paths

    def _build_operation(self, metadata: RouteMetadata) -> Dict[str, Any]:
        """Build OpenAPI operation object."""
        operation = {}

        # Basic operation info
        if metadata.summary:
            operation["summary"] = metadata.summary
        if metadata.description:
            operation["description"] = metadata.description
        if metadata.tags:
            operation["tags"] = metadata.tags
        if metadata.operation_id:
            operation["operationId"] = metadata.operation_id
        elif metadata.endpoint:
            # Use endpoint as operation ID if not explicitly set
            operation["operationId"] = metadata.endpoint
        if metadata.deprecated:
            operation["deprecated"] = True

        # Parameters
        if metadata.parameters:
            operation["parameters"] = [
                self._build_parameter(param)
                for param in metadata.parameters
            ]

        # Request body
        if metadata.request_body:
            operation["requestBody"] = {
                "required": metadata.request_body.required,
                "description": metadata.request_body.description,
                "content": {
                    metadata.request_body.content_type: {
                        "schema": metadata.request_body.schema
                    }
                }
            }

        # Responses
        if metadata.responses:
            operation["responses"] = {}
            for status_code, response in metadata.responses.items():
                operation["responses"][str(status_code)] = self._build_response(response)
        else:
            # Default response if none specified
            operation["responses"] = {
                "200": {"description": "Successful response"}
            }

        # Security
        if metadata.security:
            operation["security"] = metadata.security

        return operation

    def _build_parameter(self, param) -> Dict[str, Any]:
        """Build OpenAPI parameter object."""
        param_obj = {
            "name": param.name,
            "in": param.location,
            "required": param.required,
            "schema": param.schema,
        }

        if param.description:
            param_obj["description"] = param.description
        if param.deprecated:
            param_obj["deprecated"] = True
        if param.example is not None:
            param_obj["example"] = param.example

        return param_obj

    def _build_response(self, response) -> Dict[str, Any]:
        """Build OpenAPI response object."""
        resp_obj = {"description": response.description}

        if response.content:
            resp_obj["content"] = response.content

        if response.headers:
            resp_obj["headers"] = response.headers

        return resp_obj

    def _build_components(self) -> Dict[str, Any]:
        """Build components object (schemas, security schemes, etc.)."""
        components = {}

        # Schemas (from registry)
        schemas = openapi_registry.all_schemas()
        if schemas:
            components["schemas"] = schemas

        # Security schemes
        security_schemes = openapi_registry.all_security_schemes()
        if security_schemes:
            components["securitySchemes"] = security_schemes

        return components if components else {}

    def _convert_path_format(self, jsweb_path: str) -> str:
        """
        Convert jsweb path format to OpenAPI format.

        Examples:
            /users/<int:user_id> -> /users/{user_id}
            /files/<path:filepath> -> /files/{filepath}
            /posts/<id> -> /posts/{id}
        """
        return re.sub(r'<(?:\w+:)?(\w+)>', r'{\1}', jsweb_path)

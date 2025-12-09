"""
DTO models - Pydantic internally, jsweb API externally
"""

from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField, ValidationError
from pydantic import ConfigDict
import inspect


class JswebBaseModel(PydanticBaseModel):
    """
    Base model for DTOs in jsweb framework.

    Uses Pydantic v2 internally for fast validation and schema generation,
    but exposes a clean jsweb API for developers.

    Example:
        class UserDto(JswebBaseModel):
            name: str = Field(description="User name", max_length=100)
            email: str = Field(description="Email address", pattern=r'^\\w+@\\w+\\.\\w+$')
            age: int = Field(ge=0, le=150, description="User age")

        # Automatic validation
        user = UserDto(name="John", email="john@example.com", age=30)

        # Automatic OpenAPI schema
        schema = UserDto.openapi_schema()
    """

    model_config = ConfigDict(
        # Enable validation on assignment
        validate_assignment=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Allow arbitrary types (for custom types)
        arbitrary_types_allowed=True,
        # Extra fields behavior
        extra='forbid',  # Raise error on extra fields
        # Strict mode for better type safety
        strict=False,  # Allow coercion by default
        # Populate by name (for alias support)
        populate_by_name=True
    )

    @classmethod
    def openapi_schema(cls, *, ref_template: str = '#/components/schemas/{model}') -> Dict[str, Any]:
        """
        Generate OpenAPI 3.0 schema for this model.

        This method converts Pydantic's JSON schema to OpenAPI format,
        adding any custom jsweb metadata.

        Returns:
            OpenAPI schema dictionary
        """
        # Get Pydantic's JSON schema
        schema = cls.model_json_schema(ref_template=ref_template)

        # Add custom jsweb metadata if present (for future use)
        # Custom metadata can be added via class attributes in subclasses

        return schema

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JswebBaseModel':
        """
        Create model instance from dictionary with validation.

        Args:
            data: Dictionary to validate and parse

        Returns:
            Validated model instance

        Raises:
            ValidationError: If validation fails
        """
        return cls.model_validate(data)

    def to_dict(self, *, exclude_none: bool = False, by_alias: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary.

        Args:
            exclude_none: Exclude fields with None values
            by_alias: Use field aliases instead of field names

        Returns:
            Dictionary representation
        """
        return self.model_dump(exclude_none=exclude_none, by_alias=by_alias)

    def to_json(self, *, exclude_none: bool = False, by_alias: bool = False, indent: int = None) -> str:
        """
        Convert model to JSON string.

        Args:
            exclude_none: Exclude fields with None values
            by_alias: Use field aliases instead of field names
            indent: JSON indentation level

        Returns:
            JSON string
        """
        return self.model_dump_json(
            exclude_none=exclude_none,
            by_alias=by_alias,
            indent=indent
        )

    @classmethod
    def openapi_examples(cls) -> List[Dict[str, Any]]:
        """
        Get OpenAPI examples for this model.
        Override this method to provide custom examples.

        Returns:
            List of example dictionaries
        """
        return []

    @classmethod
    def get_model_name(cls) -> str:
        """
        Get the model name for OpenAPI components.

        Returns:
            Model name (class name by default)
        """
        return cls.__name__


def Field(
    default: Any = ...,
    *,
    # Validation constraints
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,

    # OpenAPI metadata
    title: Optional[str] = None,
    description: Optional[str] = None,
    example: Any = None,
    examples: Optional[List[Any]] = None,
    deprecated: bool = False,

    # Field behavior
    alias: Optional[str] = None,
    default_factory: Optional[callable] = None,

    # Custom extensions
    **extra: Any
) -> Any:
    """
    Define a DTO field with validation and OpenAPI metadata.

    This is jsweb's clean API that internally uses Pydantic's Field.

    Args:
        default: Default value (use ... for required fields)
        gt: Greater than
        ge: Greater than or equal
        lt: Less than
        le: Less than or equal
        multiple_of: Value must be multiple of this
        min_length: Minimum length for strings/lists
        max_length: Maximum length for strings/lists
        pattern: Regex pattern for strings
        title: Field title for OpenAPI
        description: Field description for OpenAPI
        example: Example value for OpenAPI
        examples: Multiple examples for OpenAPI
        deprecated: Mark field as deprecated
        alias: Alternative field name
        default_factory: Factory function for default value
        **extra: Additional Pydantic field parameters

    Returns:
        Field definition

    Example:
        class UserDto(JswebBaseModel):
            name: str = Field(
                description="User's full name",
                min_length=1,
                max_length=100,
                example="John Doe"
            )
            age: int = Field(
                ge=0,
                le=150,
                description="User's age in years",
                example=30
            )
            email: str = Field(
                pattern=r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$',
                description="Email address",
                example="john@example.com"
            )
    """
    # Map jsweb parameters to Pydantic Field parameters
    field_kwargs = {
        'default': default,
        'title': title,
        'description': description,
        'examples': examples or ([example] if example is not None else None),
        'deprecated': deprecated if deprecated else None,
        'alias': alias,
        'default_factory': default_factory,
        'gt': gt,
        'ge': ge,
        'lt': lt,
        'le': le,
        'multiple_of': multiple_of,
        'min_length': min_length,
        'max_length': max_length,
        'pattern': pattern,
        **extra
    }

    # Remove None values (let Pydantic use its defaults)
    field_kwargs = {k: v for k, v in field_kwargs.items() if v is not None}

    return PydanticField(**field_kwargs)


class ValidationError(ValidationError):
    """
    jsweb validation error - wraps Pydantic's ValidationError.

    Provides the same interface but can be caught as jsweb.dto.ValidationError
    without exposing Pydantic to the user.
    """
    pass

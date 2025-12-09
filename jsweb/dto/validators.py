"""
Custom validators for jsweb DTOs - wraps Pydantic's validators
"""

from pydantic import field_validator as pydantic_field_validator, model_validator as pydantic_model_validator
from typing import Any, Callable


def validator(field_name: str, *, mode: str = 'after', **kwargs) -> Callable:
    """
    Field validator decorator - jsweb API wrapping Pydantic's field_validator.

    Args:
        field_name: Name of field to validate
        mode: Validation mode ('before', 'after', 'wrap', 'plain')
        **kwargs: Additional validator parameters

    Example:
        class UserDto(JswebBaseModel):
            email: str = Field(description="Email address")

            @validator('email')
            @classmethod
            def validate_email(cls, value):
                if '@' not in value:
                    raise ValueError('Invalid email format')
                return value.lower()  # Normalize to lowercase
    """
    def decorator(func: Callable) -> Callable:
        # Use Pydantic's field_validator internally
        return pydantic_field_validator(field_name, mode=mode, **kwargs)(func)
    return decorator


def root_validator(*, mode: str = 'after', **kwargs) -> Callable:
    """
    Model-level validator decorator - validates entire model.

    Args:
        mode: Validation mode ('before', 'after', 'wrap')
        **kwargs: Additional validator parameters

    Example:
        class DateRangeDto(JswebBaseModel):
            start_date: str
            end_date: str

            @root_validator()
            @classmethod
            def validate_date_range(cls, values):
                if values['end_date'] < values['start_date']:
                    raise ValueError('end_date must be after start_date')
                return values
    """
    def decorator(func: Callable) -> Callable:
        # Use Pydantic's model_validator internally
        return pydantic_model_validator(mode=mode, **kwargs)(func)
    return decorator

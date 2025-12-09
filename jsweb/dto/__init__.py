"""
jsweb DTO System - Hybrid approach using Pydantic internally with custom API

This module provides:
- Fast validation using Pydantic v2 internally
- Custom jsweb API that's clean and framework-consistent
- Automatic OpenAPI schema generation
- Framework-wide request/response validation
"""

from .models import JswebBaseModel, Field, ValidationError
from .validators import validator, root_validator

__all__ = [
    'JswebBaseModel',
    'Field',
    'ValidationError',
    'validator',
    'root_validator',
]

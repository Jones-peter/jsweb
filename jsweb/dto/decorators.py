import functools
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field as dataclass_field

from .core import FieldMetadata, ModelT

@dataclass
class FieldConfig:
    """
    Configuration for a DTO field with runtime and OpenAPI metadata.
    """
    #validation constraints
    gt: Optional[float] = None
    ge: Optional[float] = None
    lt: Optional[float] = None
    le:Optional[float] = None
    multiple_of: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex: Optional[str] = None
    pattern: Optional[str] = None

    # Type constraints
    allow_inf_nan: bool = False
    max_digits: Optional[int] = None
    decimal_places: Optional[int] = None

    # OpenAPI metadata
    description: Optional[str] = None
    title: Optional[str] = None
    example: Any = None
    examples: Optional[List[Any]] = None
    depricated: bool = False
    format: Optional[str] = None
    read_only: bool = False
    write_only: bool = False
    nullable: bool = False

    #custom OpenAPI extensions
    custom_props: Dict[str, Any] = dataclass_field(default_factory=dict)

    #others
    alias: Optional[str] = None
    alias_priority: Optional[int] = 0
    discriminator: Optional[str] = None
    union_mode:str = 'smart'


class FieldInfoRegistry:
    """
    Global registry for field metadata with thread-safe operations.
    """
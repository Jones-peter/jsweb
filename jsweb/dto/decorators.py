from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any


@dataclass
class FieldConfig:
    """
    Configuration for a DTO field with runtime and OpenAPI metadata.
    """

    # validation constraints
    gt: float | None = None
    ge: float | None = None
    lt: float | None = None
    le: float | None = None
    multiple_of: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    regex: str | None = None
    pattern: str | None = None

    # Type constraints
    allow_inf_nan: bool = False
    max_digits: int | None = None
    decimal_places: int | None = None

    # OpenAPI metadata
    description: str | None = None
    title: str | None = None
    example: Any = None
    examples: list[Any] | None = None
    depricated: bool = False
    format: str | None = None
    read_only: bool = False
    write_only: bool = False
    nullable: bool = False

    # custom OpenAPI extensions
    custom_props: dict[str, Any] = dataclass_field(default_factory=dict)

    # others
    alias: str | None = None
    alias_priority: int | None = 0
    discriminator: str | None = None
    union_mode: str = "smart"


class FieldInfoRegistry:
    """
    Global registry for field metadata with thread-safe operations.
    """

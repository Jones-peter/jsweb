from enum import Enum
from typing import Any, Dict, TypeVar


#Type variables
T = TypeVar('T')
ModelT = TypeVar('ModelT', bound='JswebBaseModel')

class FieldMetadata:
    """
    Immutable container for field-level OpenAPI metadata.
    """
    __slots__ = (
        'title',
        'description',
        'example',
        'examples',
        'deprecated',
        'read_only',
        'write_only',
        'xml',
        'external_docs',
        'extra',
        'allow-mutation',
        'pattern',
        'format',
        'min_length',
        'max_length',
        'minimum',
        'maximum',
        'nullable',
        'regex',
        'custom_props'
    )

    def __init__(self, **kwargs: Any):
        for attr in self.__slots__:
            setattr(self, attr, kwargs.get(attr))

    def to_openapi(self) -> Dict[str, Any]:
        '''
        Convert metadata to OpenAPI-compatible dictionary.
        '''
        result: Dict[str, Any] = {}

        standard_mapping = {
            'description': 'description',
            'example': 'example',
            'deprecated': 'deprecated',
            'title': 'title',
            'pattern': 'pattern',
            'format': 'format',
            'minimum': 'minimum',
            'maximum': 'maximum',
            'exclusive_minimum': 'exclusiveMinimum',
            'exclusive_maximum': 'exclusiveMaximum',
            'min_length': 'minLength',
            'max_length': 'maxLength',
            'multiple_of': 'multipleOf',
            'read_only': 'readOnly',
            'write_only': 'writeOnly',
            'nullable': 'nullable',
        }

        for py_attr, oas_attr in standard_mapping.items():
            value = getattr(self, py_attr)
            if value is not None:
                result[oas_attr] = value
        
        if hasattr(self, 'enum') and self.enum is not None:
            if isinstance(self.enum, type) and issubclass(self.enum, Enum):
                result['enum'] = [item.value for item in self.enum]
            else:
                result['enum'] = list(self.enum)
        
        # Custom properties (x-* extensions)
        if hasattr(self, 'custom_props') and self.custom_props:
            result.update(self.custom_props)

        return result
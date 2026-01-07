# DTOs & Data Models

JsWeb provides a powerful Data Transfer Object (DTO) system built on Pydantic v2 for automatic validation, serialization, and API documentation. DTOs are essential for building robust APIs with proper data validation.

## Table of Contents

- [What are DTOs?](#what-are-dtos)
- [JswebBaseModel](#jswebbasemodel)
- [Defining DTOs](#defining-dtos)
- [Field Types](#field-types)
- [Validation](#validation)
- [Serialization](#serialization)
- [OpenAPI Integration](#openapi-integration)
- [Practical Examples](#practical-examples)
- [Best Practices](#best-practices)

## What are DTOs?

Data Transfer Objects (DTOs) are lightweight classes that define the structure and validation rules for data flowing in and out of your API. They provide:

- **Type Safety**: Explicit type definitions
- **Validation**: Automatic validation of input data
- **Documentation**: Auto-generated API schemas
- **Serialization**: Easy conversion to/from JSON
- **IDE Support**: Full autocomplete and type checking

## JswebBaseModel

The `JswebBaseModel` is the base class for all DTOs in JsWeb. It's built on Pydantic v2 and provides a clean API for data handling.

```python
from jsweb.dto import JswebBaseModel, Field

class UserDto(JswebBaseModel):
    """DTO for user data"""
    name: str = Field(description="User's full name", max_length=100)
    email: str = Field(description="Email address")
    age: int = Field(ge=0, le=150, description="User age")
```

### Return Type: `Type[JswebBaseModel]`

When you define a DTO class, it becomes a subclass of `JswebBaseModel` with all the inherited methods.

## Defining DTOs

### Basic DTO

```python
from jsweb.dto import JswebBaseModel, Field
from typing import Optional

class CreateUserRequest(JswebBaseModel):
    """Request DTO for creating a user"""
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
```

### With Defaults

```python
from jsweb.dto import JswebBaseModel, Field
from datetime import datetime

class BlogPostDto(JswebBaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str
    published: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list)
```

### Nested DTOs

```python
from jsweb.dto import JswebBaseModel, Field
from typing import List

class AddressDto(JswebBaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class UserWithAddressDto(JswebBaseModel):
    name: str
    email: str
    address: AddressDto  # Nested DTO
```

## Field Types

JsWeb supports all Python type annotations with Pydantic validation:

### Basic Types

```python
from jsweb.dto import JswebBaseModel, Field
from typing import Optional

class BasicTypesDto(JswebBaseModel):
    # String
    name: str = Field(min_length=1, max_length=100)
    
    # Integer
    age: int = Field(ge=0, le=150)
    
    # Float
    price: float = Field(gt=0)
    
    # Boolean
    active: bool = True
    
    # Optional (can be None)
    nickname: Optional[str] = None
```

### Complex Types

```python
from jsweb.dto import JswebBaseModel, Field
from datetime import datetime, date
from typing import List, Dict

class ComplexTypesDto(JswebBaseModel):
    # Lists
    tags: List[str] = Field(default_factory=list)
    scores: List[int]
    
    # Dictionary
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    # Date/Time
    birth_date: date
    created_at: datetime
    updated_at: Optional[datetime] = None
```

### Field Constraints

```python
from jsweb.dto import JswebBaseModel, Field

class ConstrainedFieldsDto(JswebBaseModel):
    # String constraints
    username: str = Field(min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_]+$')
    
    # Numeric constraints
    age: int = Field(ge=0, le=150)
    rating: float = Field(ge=0, le=5)
    
    # List constraints
    tags: list[str] = Field(min_length=1, max_length=10)
    
    # With description (for OpenAPI)
    email: str = Field(description="User's email address")
```

## Validation

### Automatic Validation

Validation happens automatically when creating instances:

```python
from jsweb.dto import JswebBaseModel, Field
from pydantic import ValidationError

class UserDto(JswebBaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=150)

# ✓ Valid
user = UserDto(name="Alice", age=30)

# ✗ Raises ValidationError
try:
    invalid = UserDto(name="", age=200)  # Empty name, age out of range
except ValidationError as e:
    print(e.errors())
```

### Custom Validators

```python
from jsweb.dto import JswebBaseModel, Field, validator
from datetime import date

class PersonDto(JswebBaseModel):
    name: str
    birth_date: date
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('birth_date')
    def birth_date_must_be_past(cls, v):
        if v > date.today():
            raise ValueError('Birth date cannot be in the future')
        return v
```

### Root Validators

Validate multiple fields together:

```python
from jsweb.dto import JswebBaseModel, root_validator

class PasswordChangeDto(JswebBaseModel):
    old_password: str
    new_password: str
    confirm_password: str
    
    @root_validator()
    def passwords_match(cls, values):
        new_pass = values.get('new_password')
        confirm_pass = values.get('confirm_password')
        
        if new_pass != confirm_pass:
            raise ValueError('Passwords do not match')
        
        return values
```

## Serialization

### `to_dict()` → `Dict[str, Any]`

Convert DTO instance to dictionary:

```python
user = UserDto(name="Alice", email="alice@example.com", age=30)

# Basic conversion
user_dict = user.to_dict()
# Output: {'name': 'Alice', 'email': 'alice@example.com', 'age': 30}

# Exclude None values
user_dict = user.to_dict(exclude_none=True)

# Use field aliases
user_dict = user.to_dict(by_alias=True)
```

### `to_json()` → `str`

Convert DTO instance to JSON string:

```python
user = UserDto(name="Alice", email="alice@example.com", age=30)

# Basic conversion
json_str = user.to_json()
# Output: '{"name":"Alice","email":"alice@example.com","age":30}'

# Pretty-printed
json_str = user.to_json(indent=2)

# Exclude None values
json_str = user.to_json(exclude_none=True)
```

### `from_dict()` → `Type[JswebBaseModel]`

Create DTO instance from dictionary:

```python
data = {
    "name": "Bob",
    "email": "bob@example.com",
    "age": 25
}

user = UserDto.from_dict(data)
# Automatically validates!
```

### `model_validate()` → `Type[JswebBaseModel]`

Parse and validate data:

```python
json_data = '{"name": "Alice", "email": "alice@example.com", "age": 30}'

# From JSON string
import json
data = json.loads(json_data)
user = UserDto.model_validate(data)

# With validation errors
try:
    invalid = UserDto.model_validate({"name": "", "age": 200})
except ValidationError as e:
    print(e)
```

## OpenAPI Integration

### `openapi_schema()` → `Dict[str, Any]`

Generate OpenAPI 3.0 schema automatically:

```python
class UserDto(JswebBaseModel):
    """A user in the system"""
    name: str = Field(description="User's full name")
    email: str = Field(description="Email address")
    age: int = Field(ge=0, le=150, description="User age")

# Generate schema
schema = UserDto.openapi_schema()

# Output:
# {
#   "type": "object",
#   "properties": {
#     "name": {"type": "string", "description": "User's full name"},
#     "email": {"type": "string", "description": "Email address"},
#     "age": {"type": "integer", "minimum": 0, "maximum": 150, ...}
#   },
#   "required": ["name", "email", "age"]
# }
```

### Using in API Documentation

```python
from jsweb import JsWebApp
from jsweb.response import json
from jsweb.dto import JswebBaseModel, Field

class CreateUserRequest(JswebBaseModel):
    """Request body for creating a user"""
    username: str = Field(min_length=3, description="Username")
    email: str = Field(description="Email address")
    password: str = Field(min_length=8, description="Password")

class UserResponse(JswebBaseModel):
    """User response DTO"""
    id: int
    username: str
    email: str

@app.route("/api/users", methods=["POST"])
async def create_user(req) -> json:
    """
    Create a new user
    
    Request body schema:
    {schema}
    
    Response schema:
    {response_schema}
    """
    # Schema is auto-documented in API
    return json({
        "id": 1,
        "username": "john",
        "email": "john@example.com"
    })
```

## Practical Examples

### User Registration

```python
from jsweb.dto import JswebBaseModel, Field, validator
from jsweb.response import json, JSONResponse
import re

class RegisterRequest(JswebBaseModel):
    """User registration request"""
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8)
    password_confirm: str
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('email')
    def email_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

class UserResponse(JswebBaseModel):
    """Registered user response"""
    id: int
    username: str
    email: str

@app.route("/api/register", methods=["POST"])
async def register(req) -> JSONResponse:
    try:
        # Parse and validate request
        req_data = await req.json()
        register_req = RegisterRequest.from_dict(req_data)
        
        # Check password confirmation
        if register_req.password != register_req.password_confirm:
            return json(
                {"error": "Passwords don't match"},
                status_code=400
            )
        
        # Create user
        user = User.create(
            username=register_req.username,
            email=register_req.email,
            password_hash=hash_password(register_req.password)
        )
        
        # Return response
        response = UserResponse(id=user.id, username=user.username, email=user.email)
        return json(response.to_dict(), status_code=201)
        
    except ValidationError as e:
        return json(
            {"errors": e.errors()},
            status_code=422
        )
```

### API Response Wrapper

```python
from jsweb.dto import JswebBaseModel, Field
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class ApiResponse(JswebBaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    status_code: int = 200

@app.route("/api/data")
async def get_data(req) -> json:
    try:
        data = fetch_data()
        response = ApiResponse(
            success=True,
            data=data,
            status_code=200
        )
        return json(response.to_dict())
    except Exception as e:
        response = ApiResponse(
            success=False,
            error=str(e),
            status_code=500
        )
        return json(response.to_dict(), status_code=500)
```

## Best Practices

### 1. Use Type Hints Consistently

```python
# ✓ Good
class UserDto(JswebBaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0)
    email: str

# ✗ Bad
class UserDto(JswebBaseModel):
    name = Field(min_length=1)
    age = Field(ge=0)
```

### 2. Provide Field Descriptions

```python
# ✓ Good - helps with API documentation
class ProductDto(JswebBaseModel):
    name: str = Field(description="Product name")
    price: float = Field(gt=0, description="Product price in USD")
    stock: int = Field(ge=0, description="Available stock count")

# ✗ Less helpful
class ProductDto(JswebBaseModel):
    name: str
    price: float
    stock: int
```

### 3. Separate Request and Response DTOs

```python
# ✓ Good
class CreateUserRequest(JswebBaseModel):
    username: str
    email: str
    password: str

class UserResponse(JswebBaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

# ✗ Less clear
class UserDto(JswebBaseModel):
    username: str
    email: str
    password: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
```

### 4. Validate Business Logic

```python
# ✓ Good
class TransferRequest(JswebBaseModel):
    from_account: int
    to_account: int
    amount: float = Field(gt=0)
    
    @root_validator()
    def accounts_different(cls, values):
        if values.get('from_account') == values.get('to_account'):
            raise ValueError('Cannot transfer to the same account')
        return values

# ✗ Less safe
class TransferRequest(JswebBaseModel):
    from_account: int
    to_account: int
    amount: float
```

### 5. Use Optional for Nullable Fields

```python
# ✓ Good
from typing import Optional

class UpdateUserRequest(JswebBaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

# ✗ Wrong
class UpdateUserRequest(JswebBaseModel):
    name: str = None  # Missing type hint
    email: str = None
```

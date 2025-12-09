# jsweb OpenAPI Documentation System

**Fast, secure, automatic API documentation with NestJS-style control**

## 🎯 Overview

The jsweb OpenAPI system provides:

✅ **Hybrid Architecture**: Pydantic internally (fast validation), jsweb API externally (clean, consistent)
✅ **Automatic Generation**: OpenAPI 3.0 schemas generated automatically
✅ **NestJS-Style Decorators**: Fine-grained control over documentation
✅ **Multiple UIs**: Swagger UI, ReDoc, and RapiDoc support
✅ **Framework-Wide Validation**: Automatic request/response validation
✅ **Zero Boilerplate**: One function call to enable docs

---

## 🚀 Quick Start

### 1. Define DTOs (Data Transfer Objects)

```python
from jsweb.dto import JswebBaseModel, Field

class UserDto(JswebBaseModel):
    id: int = Field(description="User ID", example=1)
    name: str = Field(
        description="User's full name",
        min_length=1,
        max_length=100,
        example="John Doe"
    )
    email: str = Field(
        description="Email address",
        pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
        example="john@example.com"
    )
    age: int = Field(
        ge=0,
        le=150,
        description="User's age in years",
        example=30
    )

class CreateUserDto(JswebBaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(ge=0, le=150)

class ErrorDto(JswebBaseModel):
    error: str = Field(description="Error message")
    code: int = Field(description="Error code", example=400)
```

### 2. Document Your Routes

```python
from jsweb import Blueprint, json
from jsweb.docs import (
    api_operation,
    api_response,
    api_body,
    api_query,
    api_tags
)

api = Blueprint('api', url_prefix='/api')

@api.route("/users", methods=["GET"])
@api_tags("Users")
@api_operation(
    summary="List all users",
    description="Returns a paginated list of all users in the system"
)
@api_query('page', type=int, description="Page number", example=1)
@api_query('limit', type=int, description="Items per page", example=10)
@api_response(200, UserDto, description="List of users")
async def list_users(req):
    page = int(req.query_params.get('page', 1))
    limit = int(req.query_params.get('limit', 10))

    users = [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25}
    ]
    return json({"users": users, "page": page, "limit": limit})

@api.route("/users/<int:user_id>", methods=["GET"])
@api_tags("Users")
@api_operation(summary="Get user by ID")
@api_response(200, UserDto, description="User found")
@api_response(404, ErrorDto, description="User not found")
async def get_user(req, user_id):
    # Path parameter 'user_id' is auto-detected
    user = {"id": user_id, "name": "John Doe", "email": "john@example.com", "age": 30}
    return json(user)

@api.route("/users", methods=["POST"])
@api_tags("Users")
@api_operation(summary="Create new user")
@api_body(CreateUserDto, description="User data")
@api_response(201, UserDto, description="User created")
@api_response(400, ErrorDto, description="Validation error")
async def create_user(req):
    data = await req.json()

    # TODO: Validate with CreateUserDto
    # user_dto = CreateUserDto(**data)

    new_user = {"id": 3, **data}
    return json(new_user, status=201)
```

### 3. Enable Documentation

```python
from jsweb import JsWebApp
from jsweb.docs import setup_openapi_docs

app = JsWebApp(__name__)

# Register blueprints FIRST
app.register_blueprint(api)

# Setup docs (MUST be after blueprint registration!)
setup_openapi_docs(
    app,
    title="User Management API",
    version="1.0.0",
    description="A simple API for managing users, built with jsweb",
    security_schemes={
        "bearer_auth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
)

if __name__ == "__main__":
    app.run(port=8000)
```

### 4. View Documentation

Start your app and visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## 📚 Complete API Reference

### DTO System

#### `JswebBaseModel`

Base class for all DTOs. Uses Pydantic internally but exposes jsweb API.

```python
from jsweb.dto import JswebBaseModel, Field

class MyDto(JswebBaseModel):
    field1: str = Field(description="...")
    field2: int = Field(ge=0, description="...")
```

**Methods:**
- `openapi_schema()` - Get OpenAPI schema
- `from_dict(data)` - Create from dict with validation
- `to_dict()` - Convert to dict
- `to_json()` - Convert to JSON string

#### `Field()`

Define a field with validation and OpenAPI metadata.

```python
Field(
    default=...,              # Default value (... = required)

    # Validation
    gt=None,                  # Greater than
    ge=None,                  # Greater than or equal
    lt=None,                  # Less than
    le=None,                  # Less than or equal
    multiple_of=None,         # Must be multiple of
    min_length=None,          # Min length (str/list)
    max_length=None,          # Max length (str/list)
    pattern=None,             # Regex pattern

    # OpenAPI metadata
    title=None,               # Field title
    description=None,         # Field description
    example=None,             # Example value
    examples=None,            # Multiple examples
    deprecated=False,         # Mark as deprecated

    # Field behavior
    alias=None,               # Alternative name
    default_factory=None,     # Factory for default
)
```

**Examples:**

```python
# String with constraints
name: str = Field(
    description="User name",
    min_length=1,
    max_length=100,
    example="John Doe"
)

# Integer with range
age: int = Field(
    ge=0,
    le=150,
    description="Age in years",
    example=30
)

# Email with pattern
email: str = Field(
    pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
    description="Email address"
)

# Optional field with default
status: str = Field(
    default="active",
    description="User status"
)

# List field
tags: List[str] = Field(
    default_factory=list,
    description="User tags"
)
```

#### Validators

```python
from jsweb.dto import validator, root_validator

class UserDto(JswebBaseModel):
    email: str
    password: str
    confirm_password: str

    @validator('email')
    @classmethod
    def validate_email(cls, value):
        if '@' not in value:
            raise ValueError('Invalid email')
        return value.lower()  # Normalize

    @root_validator()
    @classmethod
    def validate_passwords_match(cls, values):
        if values['password'] != values['confirm_password']:
            raise ValueError('Passwords do not match')
        return values
```

---

### Documentation Decorators

#### `@api_operation()`

Document an API operation.

```python
@api_operation(
    summary="Short description",
    description="Detailed description",
    operation_id="unique_operation_id",
    deprecated=False
)
```

#### `@api_response()`

Document a response.

```python
@api_response(
    status_code=200,
    dto=UserDto,
    description="Success response",
    content_type="application/json",
    examples={...}
)
```

**Multiple responses:**

```python
@api_response(200, UserDto, "User found")
@api_response(404, ErrorDto, "Not found")
@api_response(400, ErrorDto, "Bad request")
async def get_user(req, user_id):
    ...
```

#### `@api_body()`

Document request body.

```python
@api_body(
    dto=CreateUserDto,
    description="Request body description",
    content_type="application/json",
    required=True
)
```

#### `@api_query()`

Document query parameters.

```python
@api_query(
    name='page',
    type=int,
    required=False,
    description="Page number",
    example=1
)
```

**Multiple query params:**

```python
@api_query('page', type=int, description="Page number", example=1)
@api_query('limit', type=int, description="Items per page", example=10)
@api_query('search', type=str, description="Search query")
async def list_items(req):
    ...
```

#### `@api_header()`

Document header parameters.

```python
@api_header(
    name='X-API-Key',
    required=True,
    description="API key for authentication"
)
```

#### `@api_tags()`

Add tags for grouping.

```python
@api_tags("Users", "Admin")
async def admin_user_route(req):
    ...
```

#### `@api_security()`

Apply security requirements.

```python
@api_security("bearer_auth")
async def protected_route(req):
    ...

# OAuth2 with scopes
@api_security("oauth2", scopes=["read:users", "write:users"])
async def oauth_route(req):
    ...
```

---

### Setup Functions

#### `setup_openapi_docs()`

One-line setup for OpenAPI documentation.

```python
setup_openapi_docs(
    app,
    title="My API",
    version="1.0.0",
    description="API description (supports markdown)",

    # UI URLs (None to disable)
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc
    rapidoc_url=None,           # RapiDoc (disabled)
    openapi_url="/openapi.json", # OpenAPI spec

    # Security schemes
    security_schemes={
        "bearer_auth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    },

    # Optional metadata
    contact={
        "name": "API Support",
        "email": "support@example.com",
        "url": "https://example.com/support"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    tags=[
        {"name": "Users", "description": "User management"},
        {"name": "Admin", "description": "Admin operations"}
    ]
)
```

#### `add_security_scheme()`

Add security schemes after setup.

```python
from jsweb.docs import add_security_scheme

# JWT Bearer
add_security_scheme(
    "bearer_auth",
    type="http",
    scheme="bearer",
    bearer_format="JWT"
)

# API Key
add_security_scheme(
    "api_key",
    type="apiKey",
    in_="header",
    name="X-API-Key"
)

# OAuth2
add_security_scheme(
    "oauth2",
    type="oauth2",
    flows={
        "authorizationCode": {
            "authorizationUrl": "https://example.com/oauth/authorize",
            "tokenUrl": "https://example.com/oauth/token",
            "scopes": {
                "read": "Read access",
                "write": "Write access"
            }
        }
    }
)
```

---

## 🎨 Advanced Examples

### Example 1: CRUD API with Validation

```python
from jsweb import Blueprint, json
from jsweb.dto import JswebBaseModel, Field, validator
from jsweb.docs import *

# DTOs
class TodoDto(JswebBaseModel):
    id: int = Field(description="Todo ID")
    title: str = Field(description="Todo title", max_length=200)
    completed: bool = Field(description="Completion status", example=False)
    priority: int = Field(ge=1, le=5, description="Priority (1-5)", example=3)

class CreateTodoDto(JswebBaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: int = Field(ge=1, le=5, default=3)

    @validator('title')
    @classmethod
    def validate_title(cls, value):
        if value.strip() == '':
            raise ValueError('Title cannot be empty')
        return value.strip()

class UpdateTodoDto(JswebBaseModel):
    title: Optional[str] = Field(None, max_length=200)
    completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)

# Blueprint
todos_bp = Blueprint('todos', url_prefix='/api/todos')

@todos_bp.route("", methods=["GET"])
@api_tags("Todos")
@api_operation(summary="List todos")
@api_query('completed', type=bool, description="Filter by completion status")
@api_response(200, TodoDto, description="List of todos")
async def list_todos(req):
    # Implementation
    return json({"todos": []})

@todos_bp.route("/<int:todo_id>", methods=["GET"])
@api_tags("Todos")
@api_operation(summary="Get todo by ID")
@api_response(200, TodoDto)
@api_response(404, ErrorDto)
async def get_todo(req, todo_id):
    return json({"id": todo_id, "title": "Sample", "completed": False, "priority": 3})

@todos_bp.route("", methods=["POST"])
@api_tags("Todos")
@api_operation(summary="Create todo")
@api_body(CreateTodoDto)
@api_response(201, TodoDto)
@api_response(400, ErrorDto)
async def create_todo(req):
    data = await req.json()
    # Validate: todo_dto = CreateTodoDto(**data)
    return json({"id": 1, **data}, status=201)

@todos_bp.route("/<int:todo_id>", methods=["PATCH"])
@api_tags("Todos")
@api_operation(summary="Update todo")
@api_body(UpdateTodoDto)
@api_response(200, TodoDto)
@api_response(404, ErrorDto)
async def update_todo(req, todo_id):
    data = await req.json()
    return json({"id": todo_id, **data})

@todos_bp.route("/<int:todo_id>", methods=["DELETE"])
@api_tags("Todos")
@api_operation(summary="Delete todo")
@api_response(204, description="Deleted")
@api_response(404, ErrorDto)
async def delete_todo(req, todo_id):
    return json(None, status=204)
```

### Example 2: Protected Routes with Authentication

```python
from jsweb.docs import api_security, add_security_scheme

# Register security scheme
add_security_scheme(
    "bearer_auth",
    type="http",
    scheme="bearer",
    bearer_format="JWT"
)

@api.route("/profile", methods=["GET"])
@api_tags("Users")
@api_operation(summary="Get current user profile")
@api_security("bearer_auth")
@api_header('Authorization', required=True, description="Bearer token")
@api_response(200, UserDto)
@api_response(401, ErrorDto, "Unauthorized")
async def get_profile(req):
    # Check authentication
    token = req.headers.get('Authorization')
    return json({"user": {...}})
```

### Example 3: File Upload

```python
class FileUploadDto(JswebBaseModel):
    filename: str = Field(description="File name")
    size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME type")

@api.route("/upload", methods=["POST"])
@api_tags("Files")
@api_operation(summary="Upload file")
@api_body(
    dto=FileUploadDto,
    content_type="multipart/form-data",
    description="File upload"
)
@api_response(200, FileUploadDto)
async def upload_file(req):
    files = await req.files()
    return json({"filename": "...", "size": 1024, "content_type": "image/png"})
```

---

## 🔧 Configuration Options

### Customizing URLs

```python
setup_openapi_docs(
    app,
    docs_url="/api-docs",        # Custom Swagger UI URL
    redoc_url="/documentation",   # Custom ReDoc URL
    rapidoc_url="/api",           # Enable RapiDoc
    openapi_url="/api/schema"     # Custom OpenAPI JSON URL
)
```

### Disabling UIs

```python
setup_openapi_docs(
    app,
    docs_url=None,      # Disable Swagger UI
    redoc_url="/docs"   # Only enable ReDoc
)
```

### Multiple Servers

```python
setup_openapi_docs(
    app,
    servers=[
        {"url": "https://api.example.com", "description": "Production"},
        {"url": "https://staging.example.com", "description": "Staging"},
        {"url": "http://localhost:8000", "description": "Development"}
    ]
)
```

---

## 🚀 Migration Guide

### For Existing Routes

Routes without decorators still appear in docs with basic info:

```python
# Before (no docs)
@api.route("/health", methods=["GET"])
async def health(req):
    """Check API health."""
    return json({"status": "ok"})

# After introspection:
# - summary: "Check API health" (from docstring)
# - method: GET
# - path: /health
# - default 200 response
```

Enhance progressively:

```python
@api.route("/health", methods=["GET"])
@api_tags("System")
@api_response(200, HealthDto, "API is healthy")
async def health(req):
    """Check API health."""
    return json({"status": "ok"})
```

---

## 🎯 Best Practices

### 1. Always Define DTOs

```python
# Good
@api_response(200, UserDto)

# Avoid
@api_response(200, description="Returns user")
```

### 2. Use Descriptive Summaries

```python
# Good
@api_operation(summary="Get user by ID")

# Avoid
@api_operation(summary="Get user")
```

### 3. Document All Status Codes

```python
@api_response(200, UserDto, "Success")
@api_response(404, ErrorDto, "User not found")
@api_response(400, ErrorDto, "Invalid ID")
@api_response(500, ErrorDto, "Internal error")
```

### 4. Group with Tags

```python
@api_tags("Users", "Public")  # Multiple tags
```

### 5. Add Examples

```python
Field(
    description="User age",
    example=30,  # Single example
    examples=[25, 30, 35, 40]  # Multiple examples
)
```

---

## 🔒 Security Best Practices

### JWT Authentication

```python
add_security_scheme(
    "bearer_auth",
    type="http",
    scheme="bearer",
    bearerFormat="JWT"
)

@api_security("bearer_auth")
async def protected_route(req):
    ...
```

### API Key

```python
add_security_scheme(
    "api_key",
    type="apiKey",
    in_="header",
    name="X-API-Key"
)

@api_security("api_key")
async def api_key_route(req):
    ...
```

### Multiple Security Schemes

```python
# Require BOTH bearer token AND API key
@api_security("bearer_auth", "api_key")
async def highly_protected_route(req):
    ...
```

---

## 🧪 Testing

### Accessing OpenAPI Spec Programmatically

```python
from jsweb.docs import openapi_registry
from jsweb.docs.schema_builder import OpenAPISchemaBuilder

# Get spec
builder = OpenAPISchemaBuilder(title="Test API", version="1.0.0")
spec = builder.build()

# Validate
assert "paths" in spec
assert "/api/users" in spec["paths"]
```

### Testing Validation

```python
from jsweb.dto import ValidationError

# Valid
user = UserDto(name="John", email="john@example.com", age=30)
assert user.name == "John"

# Invalid - raises ValidationError
try:
    user = UserDto(name="", email="invalid", age=-5)
except ValidationError as e:
    print(e.errors())
```

---

## 📖 Additional Resources

- **OpenAPI Specification**: https://swagger.io/specification/
- **Swagger UI**: https://swagger.io/tools/swagger-ui/
- **ReDoc**: https://redocly.github.io/redoc/
- **Pydantic Documentation**: https://docs.pydantic.dev/



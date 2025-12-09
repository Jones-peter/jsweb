"""
Example jsweb API with OpenAPI Documentation

This example demonstrates:
- DTO definitions with validation
- NestJS-style route documentation
- Automatic OpenAPI generation
- Swagger UI and ReDoc interfaces
"""

from jsweb import JsWebApp, Blueprint
try:
    from jsweb.response import JSONResponse as json
except ImportError:
    # Fallback for this example
    def json(data, status=200):
        import json as json_module
        return {
            'status': status,
            'headers': {'Content-Type': 'application/json'},
            'body': json_module.dumps(data)
        }

# Import DTO system
from jsweb.dto import JswebBaseModel, Field, validator

# Import documentation decorators
from jsweb.docs import (
    setup_openapi_docs,
    api_operation,
    api_response,
    api_body,
    api_query,
    api_tags,
    api_security,
    add_security_scheme
)

# ============================================================================
# DTOs (Data Transfer Objects)
# ============================================================================

class UserDto(JswebBaseModel):
    """User data model."""
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
    role: str = Field(
        description="User role",
        example="user"
    )


class CreateUserDto(JswebBaseModel):
    """DTO for creating a new user."""
    name: str = Field(
        min_length=1,
        max_length=100,
        description="User name"
    )
    email: str = Field(
        pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
        description="Valid email address"
    )
    age: int = Field(ge=0, le=150, description="User age")

    @validator('name')
    @classmethod
    def validate_name(cls, value):
        """Validate and normalize name."""
        if value.strip() == '':
            raise ValueError('Name cannot be empty')
        return value.strip()

    @validator('email')
    @classmethod
    def validate_email(cls, value):
        """Normalize email to lowercase."""
        return value.lower()


class UpdateUserDto(JswebBaseModel):
    """DTO for updating a user (all fields optional)."""
    name: str = Field(None, min_length=1, max_length=100)
    email: str = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(None, ge=0, le=150)


class ErrorDto(JswebBaseModel):
    """Error response model."""
    error: str = Field(description="Error message")
    code: int = Field(description="Error code", example=400)
    details: dict = Field(default_factory=dict, description="Additional error details")


# ============================================================================
# API Blueprint
# ============================================================================

api = Blueprint('api', url_prefix='/api')

# Mock database
USERS_DB = [
    {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30, "role": "admin"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25, "role": "user"},
    {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35, "role": "user"},
]


@api.route("/users", methods=["GET"])
@api_tags("Users")
@api_operation(
    summary="List all users",
    description="Returns a paginated list of all users in the system. "
                "You can filter by role and search by name."
)
@api_query('page', type=int, required=False, description="Page number (starts at 1)", example=1)
@api_query('limit', type=int, required=False, description="Items per page (max 100)", example=10)
@api_query('role', type=str, required=False, description="Filter by role (admin, user)")
@api_query('search', type=str, required=False, description="Search in user names")
@api_response(200, UserDto, description="List of users")
async def list_users(req):
    """Get all users with optional filtering."""
    page = int(req.query_params.get('page', 1)) if hasattr(req, 'query_params') else 1
    limit = int(req.query_params.get('limit', 10)) if hasattr(req, 'query_params') else 10

    users = USERS_DB.copy()
    return json({
        "users": users,
        "page": page,
        "limit": limit,
        "total": len(users)
    })


@api.route("/users/<int:user_id>", methods=["GET"])
@api_tags("Users")
@api_operation(
    summary="Get user by ID",
    description="Retrieves a single user by their unique ID"
)
@api_response(200, UserDto, description="User found")
@api_response(404, ErrorDto, description="User not found")
async def get_user(req, user_id):
    """Get a specific user by ID."""
    user = next((u for u in USERS_DB if u["id"] == user_id), None)

    if not user:
        return json({
            "error": "User not found",
            "code": 404
        }, status=404)

    return json(user)


@api.route("/users", methods=["POST"])
@api_tags("Users")
@api_operation(
    summary="Create new user",
    description="Creates a new user in the system. "
                "Email must be unique."
)
@api_body(CreateUserDto, description="User data")
@api_response(201, UserDto, description="User created successfully")
@api_response(400, ErrorDto, description="Validation error")
@api_response(409, ErrorDto, description="Email already exists")
async def create_user(req):
    """Create a new user."""
    try:
        data = await req.json() if hasattr(req, 'json') else {}

        # Validate with DTO (in production)
        # user_dto = CreateUserDto(**data)

        # Check email uniqueness
        if any(u["email"] == data.get("email") for u in USERS_DB):
            return json({
                "error": "Email already exists",
                "code": 409
            }, status=409)

        # Create user
        new_user = {
            "id": len(USERS_DB) + 1,
            "role": "user",
            **data
        }
        USERS_DB.append(new_user)

        return json(new_user, status=201)

    except Exception as e:
        return json({
            "error": str(e),
            "code": 400
        }, status=400)


@api.route("/users/<int:user_id>", methods=["PATCH"])
@api_tags("Users")
@api_operation(
    summary="Update user",
    description="Updates an existing user. All fields are optional."
)
@api_body(UpdateUserDto, description="Fields to update")
@api_response(200, UserDto, description="User updated successfully")
@api_response(404, ErrorDto, description="User not found")
@api_response(400, ErrorDto, description="Validation error")
async def update_user(req, user_id):
    """Update an existing user."""
    user = next((u for u in USERS_DB if u["id"] == user_id), None)

    if not user:
        return json({
            "error": "User not found",
            "code": 404
        }, status=404)

    try:
        data = await req.json() if hasattr(req, 'json') else {}
        user.update(data)
        return json(user)
    except Exception as e:
        return json({
            "error": str(e),
            "code": 400
        }, status=400)


@api.route("/users/<int:user_id>", methods=["DELETE"])
@api_tags("Users")
@api_operation(
    summary="Delete user",
    description="Permanently deletes a user from the system"
)
@api_response(204, description="User deleted successfully")
@api_response(404, ErrorDto, description="User not found")
@api_security("bearer_auth")
async def delete_user(req, user_id):
    """Delete a user (requires authentication)."""
    global USERS_DB
    user = next((u for u in USERS_DB if u["id"] == user_id), None)

    if not user:
        return json({
            "error": "User not found",
            "code": 404
        }, status=404)

    USERS_DB = [u for u in USERS_DB if u["id"] != user_id]
    return json(None, status=204)


@api.route("/health", methods=["GET"])
@api_tags("System")
@api_operation(
    summary="Health check",
    description="Check if the API is running"
)
@api_response(200, description="API is healthy")
async def health_check(req):
    """Check API health."""
    return json({"status": "ok", "version": "1.0.0"})


# ============================================================================
# App Setup
# ============================================================================

def create_app():
    """Create and configure the jsweb application."""
    app = JsWebApp(__name__)

    # Register blueprints FIRST
    app.register_blueprint(api)

    # Setup OpenAPI documentation (MUST be after blueprint registration!)
    setup_openapi_docs(
        app,
        title="User Management API",
        version="1.0.0",
        description="""
# User Management API

A simple RESTful API for managing users, built with jsweb framework.

## Features

- ✅ CRUD operations for users
- ✅ Input validation with Pydantic
- ✅ Automatic OpenAPI documentation
- ✅ JWT authentication support
- ✅ Search and filtering

## Authentication

Some endpoints require a Bearer token. Use the **Authorize** button above to add your token.
        """,
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
            {
                "name": "Users",
                "description": "User management operations"
            },
            {
                "name": "System",
                "description": "System health and status"
            }
        ],
        security_schemes={
            "bearer_auth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT token"
            }
        }
    )

    return app


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    from jsweb.server import run

    app = create_app()

    print("\n" + "="*60)
    print("[*] Example API with OpenAPI Documentation")
    print("="*60)
    PORT = 8001
    print(f"\nStarting server on http://localhost:{PORT}")
    print("\nAvailable endpoints:")
    print(f"  > Swagger UI:    http://localhost:{PORT}/docs")
    print(f"  > ReDoc:         http://localhost:{PORT}/redoc")
    print(f"  > OpenAPI JSON:  http://localhost:{PORT}/openapi.json")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")

    # Note: reload doesn't work when passing app directly
    run(app, host="127.0.0.1", port=PORT, reload=False)

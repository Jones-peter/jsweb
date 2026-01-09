"""
Automatic request/response validation - FastAPI-style

This module provides automatic validation when DTOs are used,
with option to disable if needed.
"""

from functools import wraps

from pydantic import ValidationError as PydanticValidationError


def validate_request_body(dto_class: type):
    """
    Decorator that automatically validates request body against a DTO.

    This is automatically applied when @api_body is used.

    Args:
        dto_class: The DTO class to validate against

    Example:
        @api_body(CreateUserDto)  # Automatically adds validation
        async def create_user(req):
            # req.validated_body is the validated DTO instance
            return json(req.validated_body.to_dict())
    """

    def decorator(handler):
        @wraps(handler)
        async def wrapper(req, *args, **kwargs):
            # Parse request body
            try:
                if hasattr(req, "json"):
                    data = await req.json()
                else:
                    # Fallback for testing
                    data = {}

                # Validate with DTO
                validated = dto_class(**data)

                # Attach validated DTO to request
                req.validated_body = validated
                req.validated_data = validated.to_dict()

            except PydanticValidationError as e:
                # Return validation error response
                from jsweb.response import JSONResponse

                errors = []
                for error in e.errors():
                    errors.append(
                        {
                            "field": ".".join(str(x) for x in error["loc"]),
                            "message": error["msg"],
                            "type": error["type"],
                        }
                    )

                return JSONResponse(
                    {"error": "Validation failed", "details": errors}, status=400
                )

            except Exception as e:
                # Return generic error
                from jsweb.response import JSONResponse

                return JSONResponse(
                    {"error": "Invalid request body", "details": str(e)}, status=400
                )

            # Call original handler
            return await handler(req, *args, **kwargs)

        # Mark as validated
        wrapper._jsweb_validated = True
        wrapper._jsweb_dto_class = dto_class

        return wrapper

    return decorator


def auto_serialize_response(dto_class: type, status_code: int = 200):
    """
    Decorator that automatically serializes DTO responses to JSON.

    Example:
        @api_response(200, UserDto)  # Can optionally add auto-serialization
        async def get_user(req, user_id):
            user = UserDto(id=user_id, name="John", ...)
            return user  # Automatically converts to JSONResponse
    """

    def decorator(handler):
        @wraps(handler)
        async def wrapper(req, *args, **kwargs):
            result = await handler(req, *args, **kwargs)

            # If result is already a Response, return as-is
            if hasattr(result, "status_code") or isinstance(result, dict):
                return result

            # If result is a DTO instance, serialize it
            if hasattr(result, "to_dict"):
                from jsweb.response import JSONResponse

                return JSONResponse(result.to_dict(), status=status_code)

            # If result is a list of DTOs
            if isinstance(result, list) and result and hasattr(result[0], "to_dict"):
                from jsweb.response import JSONResponse

                return JSONResponse(
                    [item.to_dict() for item in result], status=status_code
                )

            # Return as-is
            return result

        return wrapper

    return decorator


def disable_auto_validation(handler):
    """
    Decorator to disable automatic validation for a specific route.

    Use this when you want the documentation but not the validation.

    Example:
        @api_body(CreateUserDto)
        @disable_auto_validation
        async def create_user(req):
            # Validation is skipped, but docs still generated
            data = await req.json()  # Manual handling
            return json(data)
    """
    handler._jsweb_disable_validation = True
    return handler

import asyncio
from functools import wraps

from itsdangerous import BadTimeSignature, SignatureExpired, URLSafeTimedSerializer

from .response import redirect, url_for

_serializer = None
_user_loader = None


def init_auth(secret_key: str, user_loader_func: callable):
    """
    Initializes the authentication system with a secret key and a user loader.

    This function must be called once at application startup to set up the
    components needed for session management and user retrieval.

    Args:
        secret_key: The secret key used to sign and verify session tokens.
        user_loader_func: A callable that takes a user ID and returns the
                          corresponding user object, or None if not found.
    """
    global _serializer, _user_loader
    _serializer = URLSafeTimedSerializer(secret_key)
    _user_loader = user_loader_func


def login_user(response, user):
    """
    Logs a user in by creating a secure, timestamped session cookie.

    This function serializes the user's ID and sets it in an HTTPOnly cookie
    on the provided response object.

    Args:
        response: The Response object to which the session cookie will be attached.
        user: The user object to log in. Must have an 'id' attribute.
    """
    session_token = _serializer.dumps(user.id)
    response.set_cookie("session", session_token, httponly=True)


def logout_user(response):
    """
    Logs a user out by deleting the session cookie.

    Args:
        response: The Response object from which the session cookie will be removed.
    """
    response.delete_cookie("session")


def get_current_user(request):
    """
    Retrieves the currently logged-in user from the session cookie.

    This function deserializes the session token from the request's cookies,
    validates its signature and expiration (max_age=30 days), and then uses the
    user loader to fetch the corresponding user object.

    Args:
        request: The incoming Request object.

    Returns:
        The user object if a valid session exists, otherwise None.
    """
    session_token = request.cookies.get("session")
    if not session_token:
        return None

    try:
        user_id = _serializer.loads(session_token, max_age=2592000)  # 30 days
        return _user_loader(user_id)
    except (SignatureExpired, BadTimeSignature):
        return None


def login_required(handler: callable) -> callable:
    """
    A decorator to protect a route from unauthenticated access.

    If the user is not logged in (i.e., `request.user` is not set), they are
    redirected to the login page. This decorator correctly handles both
    synchronous and asynchronous view functions.

    Args:
        handler: The view function to protect.

    Returns:
        The decorated view function.
    """

    @wraps(handler)
    async def decorated_function(request, *args, **kwargs):
        if not request.user:
            login_url = url_for(request, "auth.login")
            return redirect(login_url)

        if asyncio.iscoroutinefunction(handler):
            return await handler(request, *args, **kwargs)
        else:
            return handler(request, *args, **kwargs)

    return decorated_function


def admin_required(handler: callable) -> callable:
    """
    A decorator to protect a route, allowing access only to admin users.

    This decorator checks if `request.user` exists and has an attribute
    `is_admin` that evaluates to True. If the check fails, the user is
    redirected to the admin index page. It supports both sync and async handlers.

    Args:
        handler: The view function to protect.

    Returns:
        The decorated view function.
    """

    @wraps(handler)
    async def decorated_function(request, *args, **kwargs):
        if not request.user or not getattr(request.user, "is_admin", False):
            return redirect(url_for(request, "admin.index"))

        if asyncio.iscoroutinefunction(handler):
            return await handler(request, *args, **kwargs)
        else:
            return handler(request, *args, **kwargs)

    return decorated_function

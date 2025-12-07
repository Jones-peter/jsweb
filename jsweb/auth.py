from functools import wraps
import asyncio
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from .response import redirect, url_for, Forbidden

# This will be initialized by the JsWebApp instance
_serializer = None
_user_loader = None

def init_auth(secret_key, user_loader_func):
    """Initializes the authentication system."""
    global _serializer, _user_loader
    _serializer = URLSafeTimedSerializer(secret_key)
    _user_loader = user_loader_func

def login_user(response, user):
    """Logs a user in by creating a secure session cookie."""
    session_token = _serializer.dumps(user.id)
    response.set_cookie("session", session_token, httponly=True)

def logout_user(response):
    """Logs a user out by deleting the session cookie."""
    response.delete_cookie("session")

def get_current_user(request):
    """Gets the currently logged-in user from the session cookie."""
    session_token = request.cookies.get("session")
    if not session_token:
        return None

    try:
        # The max_age check (e.g., 30 days) is handled by the serializer
        user_id = _serializer.loads(session_token, max_age=2592000)
        return _user_loader(user_id)
    except (SignatureExpired, BadTimeSignature):
        return None

def login_required(handler):
    """
    A decorator to protect routes from unauthenticated access.
    It supports both sync and async handlers.
    """
    @wraps(handler)
    async def decorated_function(request, *args, **kwargs):
        if not request.user:
            login_url = url_for(request, 'auth.login')
            return redirect(login_url)
        
        # Await the handler if it's a coroutine function
        if asyncio.iscoroutinefunction(handler):
            return await handler(request, *args, **kwargs)
        else:
            return handler(request, *args, **kwargs)
    return decorated_function

def admin_required(handler):
    """
    A decorator to protect routes from non-admin access.
    It supports both sync and async handlers.
    """
    @wraps(handler)
    async def decorated_function(request, *args, **kwargs):
        if not request.user or not getattr(request.user, 'is_admin', False):
            return redirect(url_for(request, 'admin.index'))
        
        # Await the handler if it's a coroutine function
        if asyncio.iscoroutinefunction(handler):
            return await handler(request, *args, **kwargs)
        else:
            return handler(request, *args, **kwargs)
    return decorated_function

# jsweb/security.py
"""
This module provides security-related helpers, abstracting the underlying libraries.
"""
import asyncio
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

def never_cache(view):
    """
    A decorator to add headers to a response to prevent browser caching.
    This is crucial for pages that show sensitive or user-specific data,
    like a profile page, to prevent the back-forward cache from showing
    stale, logged-in content after a user has logged out.
    """
    @wraps(view)
    async def wrapper(req, *args, **kwargs):
        # Check if the view is a coroutine function or a regular function
        if asyncio.iscoroutinefunction(view):
            response = await view(req, *args, **kwargs)
        else:
            response = view(req, *args, **kwargs)
        
        # Add the headers to prevent caching
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    return wrapper

__all__ = [
    "generate_password_hash",
    "check_password_hash",
    "never_cache"
]

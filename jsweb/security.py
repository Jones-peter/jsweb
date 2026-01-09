"""
This module provides security-related helpers, abstracting underlying libraries
for common tasks like password hashing and cache control.
"""

import asyncio
from functools import wraps

from werkzeug.security import check_password_hash, generate_password_hash


def never_cache(view):
    """
    A decorator to add headers to a response to prevent browser caching.

    This is crucial for pages that show sensitive or user-specific data,
    like a profile page, to prevent the back-forward cache from showing
    stale, logged-in content after a user has logged out. It sets the
    'Cache-Control', 'Pragma', and 'Expires' headers to strongly discourage
    caching by browsers and proxies.

    Args:
        view (callable): The view function to wrap.

    Returns:
        callable: The wrapped view function.
    """

    @wraps(view)
    async def wrapper(req, *args, **kwargs):
        """
        Executes the view, then modifies the response headers to prevent caching.
        """
        if asyncio.iscoroutinefunction(view):
            response = await view(req, *args, **kwargs)
        else:
            response = view(req, *args, **kwargs)

        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    return wrapper


__all__ = ["generate_password_hash", "check_password_hash", "never_cache"]

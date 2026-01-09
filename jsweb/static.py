"""
This module provides functionality for serving static files from the filesystem.
"""

import mimetypes
import os

from .response import HTMLResponse, Response


def serve_static(request_path: str, static_url: str, static_dir: str) -> Response:
    """
    Serves a static file from a directory with security checks.

    This function safely maps a URL path to a file on the local filesystem. It
    prevents directory traversal attacks by ensuring the resolved file path is
    within the designated static directory.

    Args:
        request_path (str): The full request path (e.g., '/static/css/style.css').
        static_url (str): The URL prefix for static files (e.g., '/static').
        static_dir (str): The local directory where static files are stored.

    Returns:
        A Response object containing the file content if found and accessible,
        or an appropriate HTTP error response (403, 404, 500).
    """
    if not request_path.startswith(static_url):
        return HTMLResponse("404 Not Found", status_code=404)

    relative_path = request_path[len(static_url) :].lstrip("/")

    base_dir = os.path.abspath(static_dir)
    full_path = os.path.normpath(os.path.join(base_dir, relative_path))

    if not full_path.startswith(base_dir):
        return HTMLResponse("403 Forbidden", status_code=403)

    if not os.path.isfile(full_path):
        return HTMLResponse("404 Not Found", status_code=404)

    try:
        with open(full_path, "rb") as f:
            content = f.read()
    except OSError:
        return HTMLResponse("500 Internal Server Error", status_code=500)

    content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"

    return Response(content, status_code=200, content_type=content_type)

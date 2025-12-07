# jsweb/static.py

import os
import mimetypes
from typing import Tuple, List, Union
from .response import Response, HTMLResponse

def serve_static(
    request_path: str, static_url: str, static_dir: str
) -> Response:
    """
    Serves a static file from the configured static directory with enhanced
    security and path handling.

    Args:
        request_path: The full request path (e.g., '/static/css/style.css').
        static_url: The URL prefix for static files (e.g., '/static').
        static_dir: The local directory where static files are stored (e.g., 'static').

    Returns:
        A Response object.
    """
    # 1. More robustly calculate the relative path of the requested file
    # This avoids complex string replacement and is easier to read.
    if not request_path.startswith(static_url):
        # This case shouldn't happen if called from app.py, but it's a good safeguard.
        return HTMLResponse("404 Not Found", status_code=404)

    relative_path = request_path[len(static_url) :].lstrip("/")

    # 2. Construct the full, absolute path to the file
    base_dir = os.path.abspath(static_dir)
    # Normalize the path to resolve any '..' or '.' segments.
    full_path = os.path.normpath(os.path.join(base_dir, relative_path))

    # 3. Security Check: Prevent directory traversal attacks.
    # This is the most important security step. It ensures the final, normalized
    # path is still safely inside the designated static directory.
    if not full_path.startswith(base_dir):
        return HTMLResponse("403 Forbidden", status_code=403)

    # 4. Check if the path points to an actual file (not a directory)
    if not os.path.isfile(full_path):
        return HTMLResponse("404 Not Found", status_code=404)

    # 5. Read the file and determine its MIME type
    try:
        with open(full_path, "rb") as f:
            content = f.read()
    except IOError:
        # This can happen due to file permission errors.
        return HTMLResponse("500 Internal Server Error", status_code=500)

    content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
    
    return Response(content, status_code=200, content_type=content_type)

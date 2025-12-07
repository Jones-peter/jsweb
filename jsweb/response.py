# D:/jones/Python/jsweb/jsweb/response.py
import json as pyjson
import logging
import re
from typing import List, Tuple, Union
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
import os

logger = logging.getLogger(__name__)

# --- Script Injection ---
# Read our native AJAX script into memory once at startup for efficiency.
_JSWEB_SCRIPT_CONTENT = ""
try:
    script_path = os.path.join(os.path.dirname(__file__), "static", "jsweb.js")
    with open(script_path, "r") as f:
        _JSWEB_SCRIPT_CONTENT = f.read()
except FileNotFoundError:
    logger.warning("jsweb.js not found. Automatic AJAX functionality will be disabled.")

# --- End Script Injection ---

# Global template environment, configured by the application
_template_env = None

def configure_template_env(template_paths: Union[str, List[str]]):
    """Configures the global Jinja2 template environment."""
    global _template_env
    _template_env = Environment(
        loader=FileSystemLoader(template_paths),
        autoescape=select_autoescape(['html', 'xml'])
    )

def url_for(req, endpoint: str, **kwargs) -> str:
    """
    Generates a URL for the given endpoint.
    """
    # Handle blueprint static files
    if '.' in endpoint:
        blueprint_name, static_endpoint = endpoint.split('.', 1)
        if static_endpoint == 'static':
            for bp in req.app.blueprints_with_static_files:
                if bp.name == blueprint_name:
                    filename = kwargs.get('filename', '')
                    return f"{bp.static_url_path}/{filename}"

    # A special case for main app static files
    if endpoint == 'static':
        static_url = getattr(req.app.config, "STATIC_URL", "/static")
        filename = kwargs.get('filename', '')
        return f"{static_url}/{filename}"

    path = req.app.router.endpoints.get(endpoint)
    if path is None:
        raise ValueError(f"Endpoint '{endpoint}' not found.")

    # Replace path parameters with values from kwargs
    for key, value in kwargs.items():
        path = re.sub(rf"<\w+:{key}>", str(value), path)

    if "<" in path and ">" in path:
        raise ValueError(f"Missing URL parameters for endpoint '{endpoint}': required parameters are in the path '{path}'")

    return path

# A comprehensive mapping of common status codes to their reason phrases.
HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


class Response:
    """
    A base class for HTTP responses. It encapsulates the body, status, and headers.
    """
    default_content_type = "text/plain"

    def __init__(
            self,
            body: Union[str, bytes],
            status_code: int = 200,
            headers: dict = None,
            content_type: str = None,
    ):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}

        final_content_type = content_type or self.default_content_type
        if "content-type" not in self.headers:
            self.headers["content-type"] = final_content_type

    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: int = None,
        expires: datetime = None,
        path: str = "/",
        domain: str = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str = 'Lax',
    ):
        """Sets a cookie in the response headers."""
        cookie_val = f"{key}={value}"
        if max_age is not None:
            cookie_val += f"; Max-Age={max_age}"
        if expires is not None:
            cookie_val += f"; Expires={expires.strftime('%a, %d %b %Y %H:%M:%S GMT')}"
        if path is not None:
            cookie_val += f"; Path={path}"
        if domain is not None:
            cookie_val += f"; Domain={domain}"
        if samesite is not None:
            cookie_val += f"; SameSite={samesite}"
        if secure:
            cookie_val += "; Secure"
        if httponly:
            cookie_val += "; HttpOnly"
        
        # The 'Set-Cookie' header can appear multiple times
        if "Set-Cookie" in self.headers:
            self.headers["Set-Cookie"] += f"\n{cookie_val}"
        else:
            self.headers["Set-Cookie"] = cookie_val


    def delete_cookie(self, key: str, path: str = "/", domain: str = None):
        """Deletes a cookie by setting its expiry date to the past."""
        self.set_cookie(key, expires=datetime(1970, 1, 1), path=path, domain=domain)

    async def __call__(self, scope, receive, send):
        """
        Sends the response to the ASGI server.
        """
        body_bytes = self.body if isinstance(self.body, bytes) else self.body.encode("utf-8")
        if "content-length" not in self.headers:
            self.headers["content-length"] = str(len(body_bytes))

        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": [[k.encode(), v.encode()] for k, v in self.headers.items()],
        })
        await send({
            "type": "http.response.body",
            "body": body_bytes,
        })


class HTMLResponse(Response):
    """
    A specific response class for HTML content.
    This class automatically injects the JsWeb AJAX script into full HTML pages.
    """
    default_content_type = "text/html"

    async def __call__(self, scope, receive, send):
        """
        Sends the response, injecting the AJAX script if it's a full HTML document.
        """
        body_str = self.body if isinstance(self.body, str) else self.body.decode("utf-8")

        # Check if this is a full HTML document and not just a fragment.
        # We also check if the script content is available.
        is_full_page = "</html>" in body_str.lower()
        if is_full_page and _JSWEB_SCRIPT_CONTENT:
            # Inject the script right before the closing </head> tag.
            # This is more reliable than injecting before </body>.
            script_tag = f"<script>{_JSWEB_SCRIPT_CONTENT}</script>"
            injection_point = body_str.lower().rfind("</head>")
            
            if injection_point != -1:
                body_str = body_str[:injection_point] + script_tag + body_str[injection_point:]

        # Re-encode the body and call the parent's send method.
        self.body = body_str.encode("utf-8")
        await super().__call__(scope, receive, send)


class JSONResponse(Response):
    """
    A specific response class for JSON content.
    It automatically handles dumping the data to a JSON string.
    """
    default_content_type = "application/json"

    def __init__(
            self,
            data: any,
            status_code: int = 200,
            headers: dict = None,
    ):
        body = pyjson.dumps(data)
        super().__init__(body, status_code, headers)


class RedirectResponse(Response):
    """
    A specific response class for HTTP redirects.
    """
    def __init__(
        self,
        url: str,
        status_code: int = 302,  # Default to a temporary redirect
        headers: dict = None,
    ):
        super().__init__(body="", status_code=status_code, headers=headers)
        self.headers["location"] = url

class Forbidden(Response):
    """A specific response class for 403 Forbidden errors."""
    def __init__(self, body="403 Forbidden"):
        super().__init__(body, status_code=403, content_type="text/html")

def render(req, template_name: str, context: dict = None) -> "HTMLResponse":
    """
    Renders a Jinja2 template into an HTMLResponse.
    
    If the request is an AJAX request (sent by our script), it will first
    try to render a "partial" version of the template by looking in a
    `partials/` subdirectory. If not found, it falls back to the main template.
    """
    if _template_env is None:
        raise RuntimeError(
            "Template environment not configured. "
            "Please ensure the JsWebApp is initialized correctly."
        )

    if context is None:
        context = {}

    # Check if this is an AJAX request from our script
    is_ajax = req.headers.get("x-requested-with") == "XMLHttpRequest"
    context['is_ajax'] = is_ajax

    final_template_name = template_name
    if is_ajax:
        # Try to find a partial template first
        try:
            partial_name = os.path.join("partials", template_name)
            _template_env.get_template(partial_name)
            final_template_name = partial_name
        except TemplateNotFound:
            # If no partial exists, we'll just render the full page
            # and the script will swap the body.
            pass

    if hasattr(req, 'csrf_token'):
        context['csrf_token'] = req.csrf_token
    
    # Make url_for available in all templates
    context['url_for'] = lambda endpoint, **kwargs: url_for(req, endpoint, **kwargs)

    template = _template_env.get_template(final_template_name)
    body = template.render(**context)
    return HTMLResponse(body)


def html(body: str, status_code: int = 200, headers: dict = None) -> HTMLResponse:
    return HTMLResponse(body, status_code=status_code, headers=headers)

def json(data: any, status_code: int = 200, headers: dict = None) -> JSONResponse:
    return JSONResponse(data, status_code=status_code, headers=headers)

def redirect(url: str, status_code: int = 302, headers: dict = None) -> RedirectResponse:
    return RedirectResponse(url, status_code=status_code, headers=headers)

from __future__ import annotations

import json as pyjson
import logging
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

logger = logging.getLogger(__name__)

_JSWEB_SCRIPT_CONTENT = ""
try:
    script_path = os.path.join(os.path.dirname(__file__), "static", "jsweb.js")
    with open(script_path) as f:
        _JSWEB_SCRIPT_CONTENT = f.read()
except FileNotFoundError:
    logger.warning("jsweb.js not found. Automatic AJAX functionality will be disabled.")

_template_env = None


def configure_template_env(template_paths: str | list[str]):
    """
    Configures the global Jinja2 template environment.

    Args:
        template_paths (Union[str, List[str]]): A path or list of paths to the template directories.
    """
    global _template_env
    _template_env = Environment(
        loader=FileSystemLoader(template_paths),
        autoescape=select_autoescape(["html", "xml"]),
    )


def url_for(req, endpoint: str, **kwargs) -> str:
    """
    Generates a URL for a given endpoint.

    This function acts as a wrapper around the application's router, providing a
    consistent way to generate URLs within request handlers and templates. It also
    handles special cases for serving static files from the main app and blueprints.

    Args:
        req: The request object, used to access the application and router.
        endpoint (str): The endpoint name, which can be a view function name or a
                      special endpoint like 'static' or 'blueprint_name.static'.
        **kwargs: The arguments to build the URL, including path parameters and
                  the 'filename' for static files.

    Returns:
        str: The generated URL.
    """
    if "." in endpoint:
        blueprint_name, static_endpoint = endpoint.split(".", 1)
        if static_endpoint == "static":
            for bp in req.app.blueprints_with_static_files:
                if bp.name == blueprint_name:
                    filename = kwargs.get("filename", "")
                    return f"{bp.static_url_path}/{filename}"

    if endpoint == "static":
        static_url = getattr(req.app.config, "STATIC_URL", "/static")
        filename = kwargs.get("filename", "")
        return f"{static_url}/{filename}"

    return req.app.router.url_for(endpoint, **kwargs)


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
    A base class for HTTP responses, encapsulating the body, status code, and headers.

    Args:
        body (Union[str, bytes]): The response body.
        status_code (int): The HTTP status code.
        headers (dict, optional): A dictionary of response headers.
        content_type (str, optional): The content type of the response. If not provided,
                                      `default_content_type` is used.
    """

    default_content_type = "text/plain"

    def __init__(
        self,
        body: str | bytes,
        status_code: int = 200,
        headers: dict = None,
        content_type: str = None,
    ):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}
        self._cookies = (
            []
        )  # Store cookies separately to support multiple Set-Cookie headers

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
        samesite: str = "Lax",
    ):
        """
        Sets a cookie in the response headers.

        Args:
            key (str): The name of the cookie.
            value (str): The value of the cookie.
            max_age (int, optional): The cookie's maximum age in seconds.
            expires (datetime, optional): The cookie's expiration date.
            path (str): The path for which the cookie is valid.
            domain (str, optional): The domain for which the cookie is valid.
            secure (bool): If True, the cookie is only sent over HTTPS.
            httponly (bool): If True, the cookie is not accessible via JavaScript.
            samesite (str): The SameSite policy ('Lax', 'Strict', 'None').
        """
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

        # Store cookies separately to properly support multiple Set-Cookie headers
        self._cookies.append(cookie_val)

    def delete_cookie(self, key: str, path: str = "/", domain: str = None):
        """
        Deletes a cookie by setting its expiration date to the past.

        Args:
            key (str): The name of the cookie to delete.
            path (str): The path of the cookie.
            domain (str, optional): The domain of the cookie.
        """
        self.set_cookie(key, expires=datetime(1970, 1, 1), path=path, domain=domain)

    async def __call__(self, scope, receive, send):
        """
        Sends the response to the ASGI server.

        This method encodes the body, sets the content-length header if not already
        present, and sends the response via the ASGI `send` channel.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): The ASGI receive channel.
            send (callable): The ASGI send channel.
        """
        body_bytes = (
            self.body if isinstance(self.body, bytes) else self.body.encode("utf-8")
        )
        if "content-length" not in self.headers:
            self.headers["content-length"] = str(len(body_bytes))

        # Build headers list, properly handling multiple Set-Cookie headers
        headers_list = [[k.encode(), v.encode()] for k, v in self.headers.items()]

        # Add each cookie as a separate Set-Cookie header (proper HTTP specification)
        for cookie in self._cookies:
            headers_list.append([b"set-cookie", cookie.encode()])

        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": headers_list,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body_bytes,
            }
        )


class HTMLResponse(Response):
    """
    A response class specifically for HTML content.

    It automatically injects the `jsweb.js` AJAX script into full HTML documents
    to enable seamless client-side navigation.
    """

    default_content_type = "text/html"

    async def __call__(self, scope, receive, send):
        """
        Sends the HTML response, injecting the AJAX script if applicable.

        The script is injected before the closing `</head>` tag of any response that
        appears to be a full HTML document.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): The ASGI receive channel.
            send (callable): The ASGI send channel.
        """
        body_str = (
            self.body if isinstance(self.body, str) else self.body.decode("utf-8")
        )

        is_full_page = "</html>" in body_str.lower()
        if is_full_page and _JSWEB_SCRIPT_CONTENT:
            script_tag = f"<script>{_JSWEB_SCRIPT_CONTENT}</script>"
            injection_point = body_str.lower().rfind("</head>")

            if injection_point != -1:
                body_str = (
                    body_str[:injection_point] + script_tag + body_str[injection_point:]
                )

        self.body = body_str.encode("utf-8")
        await super().__call__(scope, receive, send)


class JSONResponse(Response):
    """
    A response class for JSON content.

    It automatically serializes the provided Python data structure into a JSON string.

    Args:
        data (any): The Python data to be serialized to JSON.
        status_code (int): The HTTP status code.
        headers (dict, optional): A dictionary of response headers.
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
    A response class for HTTP redirects.

    Args:
        url (str): The URL to redirect to.
        status_code (int): The HTTP status code for the redirect (e.g., 302, 301).
        headers (dict, optional): A dictionary of response headers.
    """

    def __init__(
        self,
        url: str,
        status_code: int = 302,
        headers: dict = None,
    ):
        super().__init__(body="", status_code=status_code, headers=headers)
        self.headers["location"] = url


class Forbidden(Response):
    """
    A convenience response class for a 403 Forbidden error.

    Args:
        body (str): The response body, defaulting to "403 Forbidden".
    """

    def __init__(self, body="403 Forbidden"):
        super().__init__(body, status_code=403, content_type="text/html")


def render(req, template_name: str, context: dict = None) -> HTMLResponse:
    """
    Renders a Jinja2 template into an HTMLResponse.

    This function automatically adds `url_for` and CSRF tokens to the template
    context. It also supports rendering partial templates for AJAX requests.

    Args:
        req: The request object.
        template_name (str): The name of the template file to render.
        context (dict, optional): A dictionary of context variables to pass to the template.

    Returns:
        HTMLResponse: The rendered HTML response.

    Raises:
        RuntimeError: If the template environment has not been configured.
    """
    if _template_env is None:
        raise RuntimeError(
            "Template environment not configured. "
            "Please ensure the JsWebApp is initialized correctly."
        )

    if context is None:
        context = {}

    is_ajax = req.headers.get("x-requested-with") == "XMLHttpRequest"
    context["is_ajax"] = is_ajax

    final_template_name = template_name
    if is_ajax:
        try:
            partial_name = os.path.join("partials", template_name)
            _template_env.get_template(partial_name)
            final_template_name = partial_name
        except TemplateNotFound:
            pass

    if hasattr(req, "csrf_token"):
        context["csrf_token"] = req.csrf_token

    context["url_for"] = lambda endpoint, **kwargs: url_for(req, endpoint, **kwargs)

    template = _template_env.get_template(final_template_name)
    body = template.render(**context)
    return HTMLResponse(body)


def html(body: str, status_code: int = 200, headers: dict = None) -> HTMLResponse:
    """
    A shortcut function to create an HTMLResponse.

    Args:
        body (str): The HTML content.
        status_code (int): The HTTP status code.
        headers (dict, optional): A dictionary of response headers.

    Returns:
        HTMLResponse: The HTML response object.
    """
    return HTMLResponse(body, status_code=status_code, headers=headers)


def json(data: any, status_code: int = 200, headers: dict = None) -> JSONResponse:
    """
    A shortcut function to create a JSONResponse.

    Args:
        data (any): The Python data to be serialized to JSON.
        status_code (int): The HTTP status code.
        headers (dict, optional): A dictionary of response headers.

    Returns:
        JSONResponse: The JSON response object.
    """
    return JSONResponse(data, status_code=status_code, headers=headers)


def redirect(
    url: str, status_code: int = 302, headers: dict = None
) -> RedirectResponse:
    """
    A shortcut function to create a RedirectResponse.

    Args:
        url (str): The URL to redirect to.
        status_code (int): The HTTP status code for the redirect.
        headers (dict, optional): A dictionary of response headers.

    Returns:
        RedirectResponse: The redirect response object.
    """
    return RedirectResponse(url, status_code=status_code, headers=headers)

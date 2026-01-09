import asyncio
import json
from io import BytesIO
from urllib.parse import parse_qs

from werkzeug.formparser import parse_form_data

# Maximum request body size (10MB default, configurable)
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10 MB


class Request:
    """
    Represents an incoming HTTP request, providing an object-oriented interface
    to the request data.

    It lazily parses the request body, form data, and JSON, and provides
    access to headers, cookies, and query parameters.

    Attributes:
        scope (dict): The raw ASGI connection scope.
        receive (callable): The ASGI receive channel.
        app: The application instance.
        method (str): The HTTP method (e.g., 'GET', 'POST').
        path (str): The request path.
        query (dict): A dictionary of query parameters.
        headers (dict): A dictionary of request headers.
        cookies (dict): A dictionary of request cookies.
        user: An attribute to hold user information, typically populated by authentication middleware.
    """

    def __init__(self, scope, receive, app):
        self.scope = scope
        self.receive = receive
        self.app = app
        self.method = self.scope.get("method", "GET").upper()
        self.path = self.scope.get("path", "/")
        self.query = self._parse_query(self.scope.get("query_string", b"").decode())
        self.headers = self._parse_headers(self.scope.get("headers", []))
        self.content_type = self.headers.get("content-type", "")
        self.cookies = self._parse_cookies(self.headers)
        self.user = None

        self._body = None
        self._form = None
        self._json = None
        self._files = None
        self._is_stream_consumed = False

    async def stream(self):
        """
        Asynchronously yields chunks of the request body.

        This method should only be called once per request, as it consumes the
        underlying ASGI receive channel.

        Yields:
            bytes: A chunk of the request body.

        Raises:
            RuntimeError: If the stream has already been consumed.
        """
        if self._is_stream_consumed:
            raise RuntimeError(
                "Stream has already been consumed. Use request.body() instead."
            )

        self._is_stream_consumed = True
        while True:
            chunk = await self.receive()
            yield chunk.get("body", b"")
            if not chunk.get("more_body", False):
                break

    async def body(self):
        """
        Reads the entire request body into memory and caches it.

        This method is safe to call multiple times.

        Returns:
            bytes: The full request body.

        Raises:
            RuntimeError: If the stream was already consumed by `stream()`.
            ValueError: If the request body exceeds MAX_REQUEST_BODY_SIZE.
        """
        if self._body is None:
            if self._is_stream_consumed:
                raise RuntimeError(
                    "Request stream was already consumed via stream(). "
                    "Always use body() if you need to access the body multiple times."
                )
            chunks = []
            total_size = 0

            async for chunk in self.stream():
                chunk_size = len(chunk)
                total_size += chunk_size

                if total_size > MAX_REQUEST_BODY_SIZE:
                    raise ValueError(
                        f"Request body size ({total_size} bytes) exceeds maximum allowed "
                        f"size of {MAX_REQUEST_BODY_SIZE} bytes"
                    )

                chunks.append(chunk)

            self._body = b"".join(chunks)
        return self._body

    async def json(self):
        """
        Parses the request body as JSON and caches the result.

        If the content type is not 'application/json' or the body is empty/invalid,
        it returns an empty dictionary.

        Returns:
            dict: The parsed JSON data.
        """
        if self._json is None:
            if "application/json" in self.content_type:
                try:
                    body_bytes = await self.body()
                    self._json = json.loads(body_bytes) if body_bytes else {}
                except (json.JSONDecodeError, ValueError):
                    self._json = {}
            else:
                self._json = {}
        return self._json

    async def form(self):
        """
        Parses form data from the request body and caches it.

        Supports 'application/x-www-form-urlencoded' and 'multipart/form-data'.
        For multipart forms, this method populates both form fields and file uploads.

        Returns:
            dict: A dictionary of form fields.
        """
        if self._form is None:
            content_type = self.headers.get("content-type", "")
            if self.method in ("POST", "PUT", "PATCH"):
                if "application/x-www-form-urlencoded" in content_type:
                    body_bytes = await self.body()
                    self._form = {
                        k: v[0] for k, v in parse_qs(body_bytes.decode()).items()
                    }
                elif "multipart/form-data" in content_type:
                    await self._parse_multipart()
                else:
                    self._form = {}
            else:
                self._form = {}
        return self._form

    async def files(self):
        """
        Retrieves uploaded files from a 'multipart/form-data' request.

        Returns:
            dict: A dictionary of uploaded files, where values are `UploadedFile` instances.
        """
        if self._files is None:
            content_type = self.headers.get("content-type", "")
            if (
                self.method in ("POST", "PUT", "PATCH")
                and "multipart/form-data" in content_type
            ):
                await self._parse_multipart()
            else:
                self._files = {}
        return self._files

    def _parse_query(self, query_string):
        """Parses a URL query string into a dictionary."""
        return {k: v[0] for k, v in parse_qs(query_string).items()}

    def _parse_headers(self, raw_headers):
        """Parses raw ASGI headers into a dictionary."""
        return {k.decode(): v.decode() for k, v in raw_headers}

    def _parse_cookies(self, headers):
        """Parses the 'cookie' header into a dictionary."""
        cookie_string = headers.get("cookie", "")
        if not cookie_string:
            return {}
        cookies = {}
        for cookie in cookie_string.split("; "):
            if "=" in cookie:
                key, value = cookie.split("=", 1)
                cookies[key] = value
        return cookies

    async def _parse_multipart(self):
        """Parses a multipart form data request using Werkzeug's parser."""
        if self._form is not None and self._files is not None:
            return

        body_bytes = await self.body()

        environ = {
            "wsgi.input": BytesIO(body_bytes),
            "CONTENT_LENGTH": str(len(body_bytes)),
            "CONTENT_TYPE": self.headers.get("content-type"),
        }

        loop = asyncio.get_running_loop()
        _, form_data, files_data = await loop.run_in_executor(
            None, lambda: parse_form_data(environ)
        )

        self._form = {k: v[0] if len(v) == 1 else v for k, v in form_data.lists()}
        self._files = {
            k: UploadedFile(v[0]) if len(v) == 1 else [UploadedFile(f) for f in v]
            for k, v in files_data.lists()
        }


class UploadedFile:
    """
    A wrapper around a file uploaded in a request.

    This class provides a convenient interface to access the file's metadata
    and content, mirroring parts of the Werkzeug `FileStorage` API.

    Attributes:
        file_storage (werkzeug.datastructures.FileStorage): The underlying file object.
        filename (str): The original filename of the uploaded file.
        content_type (str): The content type of the uploaded file.
    """

    def __init__(self, file_storage):
        self.file_storage = file_storage
        self.filename = file_storage.filename
        self.content_type = file_storage.content_type
        self._cached_content = None

    def read(self):
        """
        Read the entire file content into memory and cache it.

        Returns:
            bytes: The content of the file.
        """
        if self._cached_content is None:
            self._cached_content = self.file_storage.read()
        return self._cached_content

    def save(self, destination):
        """
        Save the uploaded file to a specified destination.

        Args:
            destination (str or path-like object): The path where the file will be saved.
        """
        self.file_storage.save(destination)

    @property
    def size(self):
        """
        Get the size of the uploaded file in bytes.

        This method attempts to read the size from the stream without consuming it.
        As a fallback, it reads the content into memory to determine its length.

        Returns:
            int: The size of the file in bytes.
        """
        try:
            current_pos = self.file_storage.stream.tell()
            self.file_storage.stream.seek(0, 2)
            size = self.file_storage.stream.tell()
            self.file_storage.stream.seek(current_pos)
            return size
        except (OSError, AttributeError):
            if self._cached_content is not None:
                return len(self._cached_content)
            try:
                content = self.read()
                return len(content) if content else 0
            except Exception:
                return 0

    def __repr__(self):
        """Provides a developer-friendly representation of the uploaded file."""
        return (
            f"<UploadedFile: {self.filename} ({self.content_type}, {self.size} bytes)>"
        )

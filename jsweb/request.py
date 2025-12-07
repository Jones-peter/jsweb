from urllib.parse import parse_qs
import json
import asyncio
from io import BytesIO
from werkzeug.formparser import parse_form_data

class Request:
    def __init__(self, scope, receive, app):
        self.scope = scope
        self.receive = receive
        self.app = app
        self.method = self.scope.get("method", "GET").upper()
        self.path = self.scope.get("path", "/")
        self.query = self._parse_query(self.scope.get("query_string", b"").decode())
        self.headers = self._parse_headers(self.scope.get("headers", []))
        self.cookies = self._parse_cookies(self.headers)
        self.user = None

        self._body = None
        self._form = None
        self._json = None
        self._files = None
        self._is_stream_consumed = False

    async def stream(self):
        if self._is_stream_consumed:
            raise RuntimeError("Stream has already been consumed.")
        
        while True:
            chunk = await self.receive()
            yield chunk.get("body", b"")
            if not chunk.get("more_body", False):
                break
        self._is_stream_consumed = True

    async def body(self):
        if self._body is None:
            chunks = []
            async for chunk in self.stream():
                chunks.append(chunk)
            self._body = b"".join(chunks)
        return self._body

    async def json(self):
        if self._json is None:
            content_type = self.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body_bytes = await self.body()
                    self._json = json.loads(body_bytes) if body_bytes else {}
                except (json.JSONDecodeError, ValueError):
                    self._json = {}
            else:
                self._json = {}
        return self._json

    async def form(self):
        if self._form is None:
            content_type = self.headers.get("content-type", "")
            if self.method in ("POST", "PUT", "PATCH"):
                if "application/x-www-form-urlencoded" in content_type:
                    body_bytes = await self.body()
                    self._form = {k: v[0] for k, v in parse_qs(body_bytes.decode()).items()}
                elif "multipart/form-data" in content_type:
                    await self._parse_multipart()
                else:
                    self._form = {}
            else:
                self._form = {}
        return self._form

    async def files(self):
        if self._files is None:
            content_type = self.headers.get("content-type", "")
            if self.method in ("POST", "PUT", "PATCH") and "multipart/form-data" in content_type:
                await self._parse_multipart()
            else:
                self._files = {}
        return self._files

    def _parse_query(self, query_string):
        return {k: v[0] for k, v in parse_qs(query_string).items()}

    def _parse_headers(self, raw_headers):
        return {k.decode(): v.decode() for k, v in raw_headers}

    def _parse_cookies(self, headers):
        cookie_string = headers.get("cookie", "")
        if not cookie_string:
            return {}
        cookies = {}
        for cookie in cookie_string.split('; '):
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
        return cookies

    async def _parse_multipart(self):
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

        # Use .lists() to correctly handle multiple values for the same key.
        self._form = {k: v[0] if len(v) == 1 else v for k, v in form_data.lists()}
        self._files = {k: UploadedFile(v[0]) if len(v) == 1 else [UploadedFile(f) for f in v] for k, v in files_data.lists()}


class UploadedFile:
    def __init__(self, file_storage):
        self.file_storage = file_storage
        self.filename = file_storage.filename
        self.content_type = file_storage.content_type

    def read(self):
        return self.file_storage.read()

    def save(self, destination):
        self.file_storage.save(destination)

    @property
    def size(self):
        self.file_storage.stream.seek(0, 2)
        size = self.file_storage.stream.tell()
        self.file_storage.stream.seek(0) # Reset stream position after getting size
        return size

    def __repr__(self):
        return f"<UploadedFile: {self.filename} ({self.content_type})>"

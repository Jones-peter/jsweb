# Response Types

JsWeb provides a comprehensive set of response classes for handling different types of HTTP responses. All response types inherit from the base `Response` class and support both synchronous and asynchronous handlers.

## Table of Contents

- [Response Base Class](#response-base-class)
- [HTML Responses](#html-responses)
- [JSON Responses](#json-responses)
- [Redirects](#redirects)
- [Error Responses](#error-responses)
- [Helper Functions](#helper-functions)
- [Cookie Management](#cookie-management)
- [Auto-Conversion](#auto-conversion)
- [Best Practices](#best-practices)

## Response Base Class

The `Response` class is the foundation for all response types. It encapsulates the HTTP response body, status code, and headers.

```python
from jsweb.response import Response

@app.route("/")
async def home(req) -> Response:
    response = Response(
        body="Hello, World!",
        status_code=200,
        headers={"X-Custom-Header": "value"},
        content_type="text/plain"
    )
    return response
```

### Response Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `body` | `Union[str, bytes]` | Required | The response body content |
| `status_code` | `int` | 200 | HTTP status code |
| `headers` | `dict` | None | Dictionary of response headers |
| `content_type` | `str` | Depends on subclass | MIME type of the response |

### Response Methods

#### `set_cookie()` → `None`

Sets a cookie in the response.

```python
@app.route("/set-cookie")
async def set_cookie_example(req) -> Response:
    response = Response("Cookie set!")
    response.set_cookie(
        key="user_id",
        value="12345",
        max_age=3600,           # 1 hour
        path="/",
        secure=True,            # HTTPS only
        httponly=True,          # JavaScript cannot access
        samesite='Strict'       # CSRF protection
    )
    return response
```

**Parameters:**
- `key` (str): Cookie name
- `value` (str): Cookie value
- `max_age` (int, optional): Lifetime in seconds
- `expires` (datetime, optional): Expiration datetime
- `path` (str): Path scope (default: "/")
- `domain` (str, optional): Domain scope
- `secure` (bool): HTTPS only (default: False)
- `httponly` (bool): Accessible via HTTP only (default: False)
- `samesite` (str): 'Strict', 'Lax', or 'None' (default: 'Lax')

#### `delete_cookie()` → `None`

Deletes a cookie by setting its expiration to the past.

```python
@app.route("/logout")
async def logout(req) -> Response:
    response = Response("Logged out")
    response.delete_cookie("session_id")
    return response
```

## HTML Responses

`HTMLResponse` automatically sets the correct content type and injects the JsWeb JavaScript library for seamless AJAX functionality.

**Return Type:** `HTMLResponse`

```python
from jsweb.response import HTMLResponse

@app.route("/page")
async def page(req) -> HTMLResponse:
    html_content = """
    <html>
        <head><title>My Page</title></head>
        <body><h1>Hello!</h1></body>
    </html>
    """
    return HTMLResponse(html_content)
```

### Features

- Automatically injects `jsweb.js` for AJAX support
- Sets `Content-Type: text/html`
- Supports AJAX partial templates

### AJAX Template Partials

For AJAX requests (requests with `X-Requested-With: XMLHttpRequest`), JsWeb looks for partial templates:

```python
# Project structure
templates/
  page.html           # Full page template
  partials/page.html  # Partial for AJAX requests

@app.route("/content")
async def get_content(req) -> HTMLResponse:
    # AJAX requests will load partials/content.html
    # Regular requests will load content.html
    return render(req, "content.html", {})
```

## JSON Responses

`JSONResponse` automatically serializes Python objects to JSON and sets the appropriate content type.

**Return Type:** `JSONResponse`

```python
from jsweb.response import JSONResponse

@app.route("/api/users")
async def list_users(req) -> JSONResponse:
    users = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    return JSONResponse(users)
```

### Features

- Automatic JSON serialization
- Sets `Content-Type: application/json`
- Supports custom status codes

### JSON with Status Codes

```python
@app.route("/api/create", methods=["POST"])
async def create_item(req) -> JSONResponse:
    # Return 201 Created status
    return JSONResponse(
        {"id": 1, "message": "Item created"},
        status_code=201
    )
```

## Redirects

`RedirectResponse` handles HTTP redirects with proper status codes.

**Return Type:** `RedirectResponse`

```python
from jsweb.response import RedirectResponse

@app.route("/old-page")
async def old_page(req) -> RedirectResponse:
    # 302 temporary redirect (default)
    return RedirectResponse("/new-page")

@app.route("/moved")
async def moved(req) -> RedirectResponse:
    # 301 permanent redirect
    return RedirectResponse("/new-location", status_code=301)
```

### Status Codes for Redirects

| Code | Type | Use Case |
|------|------|----------|
| 301 | Permanent | Resource moved permanently |
| 302 | Temporary | Temporary redirect (default) |
| 303 | See Other | Redirect after POST (POST→GET) |
| 307 | Temporary | Like 302 but preserves HTTP method |
| 308 | Permanent | Like 301 but preserves HTTP method |

## Error Responses

### Forbidden (403)

`Forbidden` provides a convenient response for authorization failures.

**Return Type:** `Forbidden`

```python
from jsweb.response import Forbidden
from jsweb.auth import get_current_user

@app.route("/admin")
async def admin_panel(req) -> Union[HTMLResponse, Forbidden]:
    user = get_current_user(req)
    if not user or not user.is_admin:
        return Forbidden("You don't have permission to access this page")
    
    return render(req, "admin.html", {})
```

### Custom Error Responses

```python
@app.route("/api/user/<int:user_id>")
async def get_user(req, user_id) -> Union[JSONResponse, Response]:
    user = User.query.get(user_id)
    if not user:
        return JSONResponse(
            {"error": "User not found"},
            status_code=404
        )
    return JSONResponse(user.to_dict())
```

## Helper Functions

JsWeb provides convenient shortcut functions for creating responses.

### `html()` → `HTMLResponse`

Creates an HTML response with a single function call.

```python
from jsweb.response import html

@app.route("/")
async def home(req) -> HTMLResponse:
    return html("<h1>Welcome!</h1>")

# With custom status code
@app.route("/created")
async def created(req) -> HTMLResponse:
    return html("<p>Page created</p>", status_code=201)
```

### `json()` → `JSONResponse`

Creates a JSON response with a single function call.

```python
from jsweb.response import json

@app.route("/api/data")
async def get_data(req) -> JSONResponse:
    return json({"status": "ok", "data": [1, 2, 3]})

# With custom status code
@app.route("/api/error")
async def error_endpoint(req) -> JSONResponse:
    return json(
        {"error": "Invalid request"},
        status_code=400
    )
```

### `redirect()` → `RedirectResponse`

Creates a redirect response with a single function call.

```python
from jsweb.response import redirect

@app.route("/go")
async def go(req) -> RedirectResponse:
    return redirect("/home")

# With custom status code
@app.route("/moved-permanently")
async def moved(req) -> RedirectResponse:
    return redirect("/new-home", status_code=301)
```

## Auto-Conversion

JsWeb automatically converts string responses to `HTMLResponse` for convenience.

```python
@app.route("/")
async def home(req):  # No explicit return type needed
    return "Hello, World!"  # Automatically converted to HTMLResponse
```

However, explicitly typing your responses is recommended for clarity:

```python
@app.route("/")
async def home(req) -> HTMLResponse:
    return "Hello, World!"
```

## Cookie Management

### Secure Cookie Settings

```python
@app.route("/login")
async def login(req) -> Response:
    response = Response("Logged in")
    response.set_cookie(
        key="session",
        value=generate_session_token(),
        max_age=86400,      # 24 hours
        path="/",
        secure=True,        # Only send over HTTPS
        httponly=True,      # Prevent JavaScript access
        samesite='Strict'   # Prevent CSRF
    )
    return response
```

### Cookie Security Best Practices

| Setting | Recommendation | Purpose |
|---------|----------------|---------|
| `secure=True` | For production | Only send over HTTPS |
| `httponly=True` | For sensitive data | Prevent XSS attacks |
| `samesite='Strict'` | For login/session | Prevent CSRF attacks |
| `max_age` | Set appropriate TTL | Limit session duration |

### Multiple Cookies

```python
@app.route("/auth")
async def authenticate(req) -> Response:
    response = Response("Authenticated")
    
    # Set multiple cookies
    response.set_cookie("user_id", "12345")
    response.set_cookie("preferences", "dark_mode")
    response.set_cookie("auth_token", token, httponly=True)
    
    return response
```

## Best Practices

### 1. Use Type Hints

Always specify return types for clarity and IDE support:

```python
@app.route("/page")
async def page(req) -> HTMLResponse:
    return render(req, "page.html", {})
```

### 2. Handle Errors Gracefully

```python
@app.route("/api/users/<int:user_id>")
async def get_user(req, user_id) -> Union[JSONResponse, Response]:
    try:
        user = User.query.get(user_id)
        if not user:
            return JSONResponse(
                {"error": "Not found"},
                status_code=404
            )
        return JSONResponse(user.to_dict())
    except Exception as e:
        return JSONResponse(
            {"error": "Server error"},
            status_code=500
        )
```

### 3. Use Helper Functions for Simplicity

```python
# ✓ Good
return json({"status": "ok"})
return html("<h1>Title</h1>")
return redirect("/home")

# ✗ Less clear
return JSONResponse({"status": "ok"})
return HTMLResponse("<h1>Title</h1>")
return RedirectResponse("/home")
```

### 4. Secure Cookies in Production

```python
# ✓ Production-ready
response.set_cookie(
    "session",
    token,
    max_age=3600,
    secure=True,        # HTTPS only
    httponly=True,      # No JavaScript access
    samesite='Strict'   # CSRF protection
)

# ✗ Insecure
response.set_cookie("session", token)
```

### 5. Set Appropriate Status Codes

```python
# ✓ Correct
return JSONResponse({"error": "Not found"}, status_code=404)
return JSONResponse({"data": user}, status_code=200)

# ✗ Less explicit
return JSONResponse({"error": "Not found"})  # Defaults to 200
```

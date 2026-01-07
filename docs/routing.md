# Routing

Routing is the process of mapping URLs to the functions that handle them. In JsWeb, defining routes is simple and elegant using decorators.

## Table of Contents

- [Basic Routing](#basic-routing)
- [Return Types](#return-types)
- [HTTP Methods](#http-methods)
- [URL Parameters](#url-parameters)
- [Type Converters](#type-converters)
- [Route Organization with Blueprints](#route-organization-with-blueprints)
- [Advanced Patterns](#advanced-patterns)
- [Best Practices](#best-practices)

## Basic Routing

Here's a simple example of how to define a route:

```python
from jsweb import JsWebApp
import config

app = JsWebApp(config=config)

@app.route("/")
async def home(req):
    return "Hello, World!"
```

In this example, we're mapping the root URL (`/`) to the `home` function. When a user visits the root of your site, the `home` function will be called, and the string "Hello, World!" will be returned to the user's browser.

!!! note "Async Functions"
    JsWeb routes are always async functions. This allows your application to handle multiple concurrent requests efficiently.

## Return Types

All route handlers must return a **Response object** or a **string** (which is auto-converted to `HTMLResponse`).

### Valid Return Types

```python
from jsweb.response import Response, HTMLResponse, JSONResponse, RedirectResponse, html, json, redirect

# String - automatically converted to HTMLResponse
@app.route("/")
async def home(req):  # No explicit return type
    return "Hello, World!"

# HTMLResponse explicitly typed
@app.route("/page")
async def page(req) -> HTMLResponse:
    return html("<h1>Welcome</h1>")

# JSONResponse
@app.route("/api/data")
async def get_data(req) -> JSONResponse:
    return json({"status": "ok"})

# RedirectResponse
@app.route("/go")
async def go(req) -> RedirectResponse:
    return redirect("/home")

# Base Response class
@app.route("/custom")
async def custom(req) -> Response:
    return Response("Custom content", status_code=200)
```

### Return Type Reference

| Return Type | Usage | Example |
|------------|-------|---------|
| `str` | Simple HTML | `return "Hello"` |
| `HTMLResponse` | Rendered HTML | `return render(req, "template.html", {})` |
| `JSONResponse` | JSON API responses | `return json({"data": [1,2,3]})` |
| `RedirectResponse` | HTTP redirects | `return redirect("/page")` |
| `Response` | Custom responses | `return Response(body, status_code=200)` |

!!! warning "Type Mismatch"
    Ensure your return type matches the actual value returned. This helps with IDE autocomplete and catches bugs early:
    
    ```python
    # ✓ Correct
    @app.route("/api")
    async def api(req) -> JSONResponse:
        return json({"data": "value"})
    
    # ✗ Incorrect type hint
    @app.route("/page")
    async def page(req) -> JSONResponse:
        return "HTML content"  # Mismatch!
    ```

## HTTP Methods

By default, a route only responds to `GET` requests. You can specify the HTTP methods that a route should handle using the `methods` argument.

```python
@app.route("/submit", methods=["GET", "POST"])
async def submit(req):
    if req.method == "POST":
        # Handle the POST request
        return "Form submitted!"
    # Handle the GET request
    return "Please submit the form."
```

### Common HTTP Methods

| Method | Purpose |
|--------|---------|
| `GET` | Retrieve data from the server |
| `POST` | Submit data to the server |
| `PUT` | Update existing resource |
| `DELETE` | Delete a resource |
| `PATCH` | Partially update a resource |
| `HEAD` | Like GET but without the response body |

!!! tip "RESTful Routes"
    Use different HTTP methods to create RESTful APIs. For example, `GET /items` lists items, `POST /items` creates a new item, `PUT /items/1` updates item 1, and `DELETE /items/1` deletes item 1.

## URL Parameters

You can add variable sections to a URL by marking them with angle brackets (`<variable_name>`). The variable is then passed as a keyword argument to your function.

```python
@app.route("/user/<username>")
async def profile(req, username):
    return f"Hello, {username}!"
```

### Example

- URL: `/user/alice` → `username` = `"alice"`
- URL: `/user/bob` → `username` = `"bob"`

## Type Converters

You can specify a type for the URL variable to ensure it matches a specific pattern. This helps with data validation and routing specificity.

```python
@app.route("/user/id/<int:user_id>")
async def profile_by_id(req, user_id):
    return f"Hello, user number {user_id}!"
```

### Supported Type Converters

| Converter | Description | Example |
|-----------|-------------|---------|
| `string` | Matches any text without slashes (default) | `/user/john` |
| `int` | Matches positive integers | `/user/id/123` |
| `float` | Matches floating-point numbers | `/distance/5.5` |
| `path` | Like string but accepts slashes | `/files/documents/notes.txt` |
| `uuid` | Matches UUID format | `/item/550e8400-e29b-41d4-a716-446655440000` |

### Example Routes

```python
# String (default)
@app.route("/search/<query>")
async def search(req, query) -> str:
    return f"Searching for: {query}"

# Integer
@app.route("/post/<int:post_id>")
async def get_post(req, post_id) -> str:
    return f"Viewing post {post_id}"

# Float
@app.route("/temperature/<float:celsius>")
async def convert_temp(req, celsius) -> str:
    fahrenheit = (celsius * 9/5) + 32
    return f"{celsius}°C is {fahrenheit}°F"

# Path (allows slashes)
@app.route("/files/<path:filepath>")
async def serve_file(req, filepath) -> str:
    return f"Serving: {filepath}"

# UUID
@app.route("/item/<uuid:item_id>")
async def get_item(req, item_id) -> str:
    return f"Item: {item_id}"
```

!!! tip "Multiple Parameters"
    You can have multiple parameters in a single route:
    
    ```python
    @app.route("/post/<int:post_id>/comment/<int:comment_id>")
    async def get_comment(req, post_id, comment_id) -> JSONResponse:
        return json({
            "post_id": post_id,
            "comment_id": comment_id
        })
    ```

## Route Organization with Blueprints

For larger applications, use Blueprints to organize routes into logical groups:

```python
from jsweb import Blueprint

# Create a blueprint for user-related routes
user_bp = Blueprint('users', url_prefix='/users')

@user_bp.route('/')
async def user_list(req) -> JSONResponse:
    return json({"users": []})

@user_bp.route('/<int:user_id>')
async def user_detail(req, user_id) -> JSONResponse:
    return json({"user_id": user_id})

# Register in app.py
from views import user_bp
app.register_blueprint(user_bp)
```

The routes will be available at `/users/` and `/users/<user_id>`.

See [Blueprints](blueprints.md) for more details.

## Advanced Patterns

### Optional Parameters

```python
@app.route("/api/items")
@app.route("/api/items/<int:item_id>")
async def get_items(req, item_id: Optional[int] = None) -> JSONResponse:
    if item_id:
        return json({"item_id": item_id})
    return json({"items": []})
```

### Query Parameters

```python
@app.route("/search")
async def search(req) -> HTMLResponse:
    query = req.query.get('q', '')
    page = req.query.get('page', '1')
    return html(f"<p>Searching for: {query} (page {page})</p>")
```

Usage: `/search?q=python&page=2`

### Dynamic Responses

```python
from jsweb.response import JSONResponse

@app.route("/api/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
async def manage_user(req, user_id) -> JSONResponse:
    if req.method == "GET":
        return json({"user_id": user_id, "action": "retrieve"})
    elif req.method == "PUT":
        return json({"user_id": user_id, "action": "update"})
    elif req.method == "DELETE":
        return json({"user_id": user_id, "action": "delete"})
```

## Best Practices

!!! warning "Route Specificity"
    Define more specific routes before more general ones. For example, put `/users/me` before `/users/<int:user_id>`.

!!! tip "Naming Conventions"
    Use lowercase route paths and clear, descriptive function names:
    
    ```python
    @app.route("/api/users")           # ✓ Good
    @app.route("/api/Users")           # ✗ Avoid
    ```

!!! info "Documentation"
    Add docstrings to your route handlers:
    
    ```python
    @app.route("/api/items")
    async def list_items(req):
        """Retrieve all items from the database"""
        return {"items": []}
    ```

!!! note "Error Handling"
    Always handle potential errors in your routes:
    
    ```python
    @app.route("/user/<int:user_id>")
    async def get_user(req, user_id):
        user = User.query.get(user_id)
        if user is None:
            return {"error": "User not found"}, 404
        return user.to_dict()
    ```


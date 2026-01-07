# Templating

JsWeb uses the [Jinja2](https://jinja.palletsprojects.com/) templating engine to render dynamic HTML. Jinja2 is a powerful and flexible templating language that allows you to embed logic and variables directly into your HTML files.

## Table of Contents

- [Rendering Templates](#rendering-templates)
- [Return Types](#return-types)
- [Template Variables](#template-variables)
- [Control Structures](#control-structures)
- [Template Filters](#template-filters)
- [Template Inheritance](#template-inheritance)
- [Macros](#macros)
- [Custom Filters](#custom-filters)
- [Best Practices](#best-practices)

## Rendering Templates

To render a template, use the `render` function from the `jsweb.response` module:

**Return Type:** `HTMLResponse`

```python
from jsweb.response import render, HTMLResponse

@app.route("/")
async def home(req) -> HTMLResponse:
    return render(req, "index.html", {"name": "World"})
```

In this example, we're rendering the `index.html` template and passing a context dictionary with a `name` variable. The `render` function automatically looks for templates in the `templates` folder of your project.

### render() Function Signature

```python
def render(
    req: Request,
    template_name: str,
    context: dict = None
) -> HTMLResponse:
    """
    Renders a Jinja2 template into an HTMLResponse.
    
    Args:
        req: The request object
        template_name: Name of the template file
        context: Dictionary of context variables
        
    Returns:
        HTMLResponse: The rendered HTML response
    """
```

!!! tip "Template Location"
    Templates must be in a `templates` folder in your project root. JsWeb automatically discovers and serves them.

## Return Types

All templating functions return `HTMLResponse` objects:

### Helper Functions

```python
from jsweb.response import render, html, HTMLResponse

# render() returns HTMLResponse
@app.route("/page")
async def page(req) -> HTMLResponse:
    return render(req, "page.html", {"title": "My Page"})

# html() helper returns HTMLResponse
@app.route("/simple")
async def simple(req) -> HTMLResponse:
    return html("<h1>Hello</h1>")
```

### Return Type Reference

| Function | Return Type | Usage |
|----------|------------|-------|
| `render()` | `HTMLResponse` | Load and render template files |
| `html()` | `HTMLResponse` | Quick HTML response |

## Template Variables

You can use variables in your templates by enclosing them in double curly braces (`{{ ... }}`).

```html
<!-- templates/index.html -->
<h1>Hello, {{ name }}!</h1>
<p>Welcome, {{ user.username }}!</p>
<p>Items count: {{ items | length }}</p>
```

### Variable Examples with Type Hints

```python
from jsweb.response import render, HTMLResponse
from typing import List, Dict, Any

@app.route("/")
async def home(req) -> HTMLResponse:
    # Context with various types
    context: Dict[str, Any] = {
        "name": "Alice",              # str
        "user": {                     # dict
            "username": "alice",
            "email": "alice@example.com"
        },
        "items": [1, 2, 3, 4, 5],    # list
        "count": 42                   # int
    }
    return render(req, "index.html", context)
```

```html
<!-- HTML Template -->
{{ name }}              <!-- Output: Alice -->
{{ user.username }}     <!-- Output: alice -->
{{ count + 10 }}        <!-- Output: 52 -->
```

## Control Structures

### if Statements

```html
{% if user %}
  <p>Hello, {{ user.name }}!</p>
{% elif guest %}
  <p>Welcome, guest!</p>
{% else %}
  <p>Please log in.</p>
{% endif %}
```

### for Loops

```html
<ul>
  {% for item in items %}
    <li>{{ item }}</li>
  {% endfor %}
</ul>
```

### Loop Variables

Jinja2 provides special variables inside loops:

```html
<ul>
  {% for item in items %}
    <li>
      {{ loop.index }}: {{ item }}
      {% if loop.first %}(first item){% endif %}
      {% if loop.last %}(last item){% endif %}
    </li>
  {% endfor %}
</ul>
```

| Variable | Description |
|----------|-------------|
| `loop.index` | Current iteration (1-indexed) |
| `loop.index0` | Current iteration (0-indexed) |
| `loop.revindex` | Iterations remaining (descending) |
| `loop.first` | True if first iteration |
| `loop.last` | True if last iteration |
| `loop.length` | Total number of items |

### Filtering in Loops

```html
{% for user in users if user.active %}
  <p>{{ user.name }}</p>
{% endfor %}
```

## Template Filters

Filters modify variables. Use the pipe (`|`) syntax:

```html
{{ "hello" | upper }}              <!-- Output: HELLO -->
{{ "HELLO" | lower }}              <!-- Output: hello -->
{{ "hello world" | title }}        <!-- Output: Hello World -->
{{ items | length }}               <!-- Output: 3 -->
{{ price | round(2) }}             <!-- Output: 19.99 -->
{{ date | strftime('%Y-%m-%d') }} <!-- Output: 2024-01-05 -->
```

### Common Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `upper` | Convert to uppercase | `{{ text \| upper }}` |
| `lower` | Convert to lowercase | `{{ text \| lower }}` |
| `title` | Capitalize first letter of each word | `{{ text \| title }}` |
| `capitalize` | Capitalize first letter | `{{ text \| capitalize }}` |
| `length` | Get length | `{{ items \| length }}` |
| `reverse` | Reverse a list | `{{ items \| reverse }}` |
| `sort` | Sort a list | `{{ items \| sort }}` |
| `join` | Join list items | `{{ items \| join(', ') }}` |
| `default` | Provide default value | `{{ value \| default('N/A') }}` |
| `abs` | Absolute value | `{{ -5 \| abs }}` |
| `round` | Round number | `{{ 3.14159 \| round(2) }}` |
| `int` | Convert to integer | `{{ "42" \| int }}` |
| `string` | Convert to string | `{{ 42 \| string }}` |

### Chaining Filters

```html
{{ "hello world" | upper | replace('WORLD', 'JSWEB') }}
<!-- Output: HELLO JSWEB -->
```

## Template Inheritance

Template inheritance allows you to build a base template with common elements and extend it in other templates. This reduces code duplication.

### Base Template (base.html)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}My Site{% endblock %}</title>
    <link rel="stylesheet" href="{{ static('css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
    </nav>
    
    <div class="content">
        {% block content %}{% endblock %}
    </div>
    
    <footer>
        <p>&copy; 2024 My Site. All rights reserved.</p>
    </footer>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Child Template (index.html)

```html
{% extends "base.html" %}

{% block title %}Home - My Site{% endblock %}

{% block content %}
    <h1>Welcome to my site!</h1>
    <p>This is the home page.</p>
{% endblock %}
```

### Another Child Template (about.html)

```html
{% extends "base.html" %}

{% block title %}About - My Site{% endblock %}

{% block content %}
    <h1>About Us</h1>
    <p>Learn more about our site here.</p>
{% endblock %}
```

!!! tip "Block Naming"
    Use descriptive block names like `{% block title %}`, `{% block content %}`, `{% block extra_css %}` to make your templates clear and organized.

## Macros

Macros are reusable template functions. They help eliminate code duplication for complex HTML patterns.

```html
{# templates/macros.html #}

{% macro render_user(user) %}
    <div class="user-card">
        <h3>{{ user.name }}</h3>
        <p>Email: {{ user.email }}</p>
        <p>Status: {% if user.active %}Active{% else %}Inactive{% endif %}</p>
    </div>
{% endmacro %}

{% macro render_pagination(current_page, total_pages) %}
    <nav class="pagination">
        {% if current_page > 1 %}
            <a href="?page=1">First</a>
            <a href="?page={{ current_page - 1 }}">Previous</a>
        {% endif %}
        
        <span>Page {{ current_page }} of {{ total_pages }}</span>
        
        {% if current_page < total_pages %}
            <a href="?page={{ current_page + 1 }}">Next</a>
            <a href="?page={{ total_pages }}">Last</a>
        {% endif %}
    </nav>
{% endmacro %}
```

### Using Macros

```html
{% from 'macros.html' import render_user, render_pagination %}

<div class="users">
    {% for user in users %}
        {{ render_user(user) }}
    {% endfor %}
</div>

{{ render_pagination(current_page, total_pages) }}
```

## Custom Filters

Create custom filters to extend Jinja2's functionality. Filters always return a value (typically `str` or modified value):

```python
from typing import str, Any

# app.py
@app.filter("markdown")
def markdown_filter(text: str) -> str:
    """Convert markdown text to HTML"""
    import markdown
    return markdown.markdown(text)

@app.filter("slugify")
def slugify_filter(text: str) -> str:
    """Convert text to URL-safe slug"""
    return text.lower().replace(' ', '-')

@app.filter("currency")
def currency_filter(value: float) -> str:
    """Format number as currency"""
    return f"${value:.2f}"

@app.filter("ordinal")
def ordinal_filter(n: int) -> str:
    """Convert number to ordinal (1st, 2nd, etc)"""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n}st"
    elif n % 10 == 2 and n % 100 != 12:
        return f"{n}nd"
    elif n % 10 == 3 and n % 100 != 13:
        return f"{n}rd"
    else:
        return f"{n}th"
```

### Filter Return Types

| Filter | Input Type | Output Type |
|--------|-----------|-------------|
| markdown | `str` | `str` (HTML) |
| slugify | `str` | `str` |
| currency | `float` | `str` |
| ordinal | `int` | `str` |

### Using Custom Filters

```html
{{ "Hello World" | slugify }}        <!-- Output: hello-world -->
{{ 19.99 | currency }}              <!-- Output: $19.99 -->
{{ 21 | ordinal }}                  <!-- Output: 21st -->
{{ "# Heading" | markdown }}        <!-- Output: <h1>Heading</h1> -->
```

!!! tip "Filter Naming"
    Use lowercase, descriptive names for your filters. Always test them before using in production.
    {# Bad: Complex logic in template #}
    {% if user and user.is_active and user.role == 'admin' and user.permissions.can_edit %}
    
    {# Good: Simple check in template #}
    {% if can_edit %}
    ```

!!! info "Performance"
    Cache templates in production. JsWeb automatically handles this, but ensure `DEBUG=False` in production config.

!!! tip "Organization"
    Organize templates in subdirectories:
    
    ```
    templates/
    ├── base.html
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── admin/
    │   └── dashboard.html
    └── macros.html
    ```

!!! note "Comments"
    Use Jinja2 comments that won't appear in output:
    
    ```html
    {# This is a comment #}
    {# It won't appear in the rendered HTML #}
    ```


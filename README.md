<p align="center">
<a href="https://jsweb-framework.site/" target="_blank">
  <img src="https://github.com/Jones-peter/jsweb/blob/main/images/jsweb_logo.png?raw=true" alt="JsWeb Logo" width="200">
</a>
</p>
<p align="center">
  
<p align="center">
  <a href="https://pypi.org/project/jsweb/">
    <img src="https://img.shields.io/pypi/v/jsweb" alt="PyPI version"/>
  </a>
  <img src="https://img.shields.io/badge/license-MIT-red.svg" alt="License"/>
  <a href="https://pepy.tech/project/Jsweb">
    <img src="https://static.pepy.tech/personalized-badge/jsweb?period=total&units=NONE&left_color=BLUE&right_color=GREEN&left_text=downloads" alt="PyPI version"/>
  </a>
</p>

<p align="center">
  <a href="https://discord.gg/sQHNheEW">
    <img src="https://gist.githubusercontent.com/cxmeel/0dbc95191f239b631c3874f4ccf114e2/raw/discord.svg" alt="Discord"/>
  </a>
  <a href="https://jsweb-framework.site">
    <img src="https://gist.githubusercontent.com/cxmeel/0dbc95191f239b631c3874f4ccf114e2/raw/documentation_learn.svg" alt="Documentation"/>
  </a>
  <a href="https://github.com/sponsors/Jones-peter">
    <img src="https://gist.githubusercontent.com/cxmeel/0dbc95191f239b631c3874f4ccf114e2/raw/github_sponsor.svg" alt="Sponsor GitHub"/>
  </a>
  <a href="https://www.paypal.com/paypalme/jonespeter22">
    <img src="https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif" alt="PayPal Sponsor"/>
  </a>
</p>

# JsWeb: The Blazing-Fast ASGI Lightweight Python Web Framework

**JsWeb** is a modern, high-performance Python web framework built from the ground up on the **ASGI** standard. It's designed for developers who want the speed of asynchronous programming with the simplicity of a classic framework.

With built-in, zero-configuration AJAX and a focus on developer experience, JsWeb makes it easy to build fast, dynamic web applications without writing a single line of JavaScript.

## Core Features

*   **Blazing-Fast ASGI Core:** Built for speed and concurrency, compatible with servers like Uvicorn.
*   **Automatic AJAX:** Forms and navigation are automatically handled in the background for a smooth, single-page-application feel with zero configuration.
*   **Elegant Routing:** Define routes with a simple decorator syntax.
*   **Jinja2 Templating:** Render dynamic HTML with a powerful and familiar templating engine.
*   **Built-in Security:** Comes with CSRF protection, password hashing, and cache-control tools out of the box.
*   **Full-Featured Forms:** A powerful, easy-to-use form library with validation.
*   **SQLAlchemy Integration:** Includes Alembic for easy database migrations.
*   **Automatic Admin Panel:** A production-ready admin interface for your models that's generated automatically.
*   **Modular Blueprints:** Organize your code into clean, reusable components.
*   **Powerful CLI:** A command-line interface for creating projects, running the server, and managing your database.

### Contributors
<a href="https://github.com/jones-peter/jsweb/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=jones-peter/jsweb" />
</a>

## Command-Line Interface (CLI)

JsWeb comes with a powerful set of command-line tools to streamline your development workflow.

*   **`jsweb run`**: Starts the development server.
    *   `--host <address>`: Specify the host to run on (e.g., `0.0.0.0`).
    *   `--port <number>`: Specify the port.
    *   `--reload`: Enable auto-reloading on code changes.
    *   `--qr`: Display a QR code for accessing the server on your local network.

*   **`jsweb new <project_name>`**: Creates a new, production-ready JsWeb project with a clean directory structure and all necessary files.

*   **`jsweb db ...`**: A group of commands for managing your database migrations with Alembic.
    *   `jsweb db prepare -m "Your message"`: Generates a new database migration script based on changes to your models.
    *   `jsweb db upgrade`: Applies all pending migrations to the database.
    *   `jsweb db downgrade`: Reverts the last applied migration.

*   **`jsweb create-admin`**: An interactive command to create a new administrator user in the database.

## Installation & Setup

Get up and running in under a minute.

1.  **Install JsWeb:**
    ```bash
    pip install jsweb
    ```

2.  **Create a new project:**
    ```bash
    jsweb new my_project
    cd my_project
    ```

3.  **(Optional) Set up the database:**
    ```bash
    jsweb db prepare -m "Initial migration"
    jsweb db upgrade
    ```

4.  **Run the development server:**
    ```bash
    jsweb run --reload
    ```

Your new JsWeb project is now running with auto-reloading enabled!

## Quickstart: A Real-World Example

Here’s how a simple but structured JsWeb application looks, using **Blueprints** to organize your code.

**`views.py`**
```python
from jsweb import Blueprint, render

# 1. Create a "Blueprint" for a group of related pages.
views_bp = Blueprint('views')

# 2. Define a route on the blueprint.
@views_bp.route("/")
async def home(req):
    # The render function automatically finds your templates.
    return render(req, "welcome.html", {"user_name": "Guest"})
```

**`app.py`**
```python
from jsweb import JsWebApp
import config

# Import the blueprint you just created.
from views import views_bp

# 3. Create the main application instance.
app = JsWebApp(config=config)

# 4. Register your blueprint with the app.
app.register_blueprint(views_bp)

# The `jsweb run` command will find and run this `app` instance.
```

This structure allows you to organize your application into logical components, making it clean and scalable from the very beginning.

For more detailed usage, refer to the [official documentation](https://jsweb-framework.site/), individual module docstrings, and examples within the codebase.

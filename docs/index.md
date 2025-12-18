---
hide:
  - navigation
  - toc
---

<style>
  .md-typeset h1 {
    display: none;
  }
</style>

<p align="center">
  <img src="https://github.com/Jsweb-Tech/jsweb/blob/main/images/jsweb-main-logo.png?raw=true" alt="JsWeb Logo" width="300">
</p>

<p align="center">
    <em>The Blazing-Fast, Modern ASGI Python Web Framework.</em>
</p>

<p align="center">
<a href="https://pypi.org/project/jsweb/" target="_blank">
    <img src="https://img.shields.io/pypi/v/jsweb?color=%2334D058&label=pypi%20package" alt="PyPI version">
</a>
<a href="https://pypi.org/project/jsweb/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/jsweb.svg?color=%2334D058" alt="Supported Python versions">
</a>
<a href="https://github.com/Jsweb-Tech/jsweb/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/Jsweb-Tech/jsweb.svg?color=%2334D058" alt="License">
</a>
</p>

---

**JsWeb** is a blazing-fast, lightweight ASGI Python web framework that combines traditional MVC architecture and modern API-first development into a single, unified technology.
Build full-stack web apps and APIs together without switching frameworks.

## ✨ Key Features

*   **🚀 Blazing Fast**: Built on ASGI, JsWeb is designed for high concurrency and performance.
*   **🔄 Zero-Config AJAX**: Forms and navigation are automatically handled in the background, giving your app a Single Page Application (SPA) feel without writing JavaScript.
*   **🛡️ Built-in Security**: CSRF protection, secure session management, and password hashing are enabled by default.
*   **🗄️ Database Ready**: Integrated SQLAlchemy support with Alembic migrations makes database management a breeze.
*   **⚙️ Admin Interface**: A production-ready admin panel is generated automatically for your models.
*   **🧩 Modular Design**: Use Blueprints to organize your application into reusable components.
*   **🎨 Jinja2 Templating**: Powerful and familiar templating engine for rendering dynamic HTML.
*   **🛠️ Powerful CLI**: A comprehensive command-line tool for scaffolding, running, and managing your project.

## ⚡ Quick Start

Get up and running in seconds.

### 1. Install JsWeb

```bash
pip install jsweb
```

### 2. Create a Project

```bash
jsweb new my_awesome_app
cd my_awesome_app
```

### 3. Run the Server

```bash
jsweb run --reload
```

Visit `http://127.0.0.1:8000` and you'll see your new app running!

## 📝 Example Code

Here is a simple example of a JsWeb application:

```python
from jsweb import JsWebApp, render
import config

app = JsWebApp(config=config)

@app.route("/")
async def home(req):
    return render(req, "index.html", {"message": "Hello from JsWeb!"})

@app.route("/api/data")
async def get_data(req):
    return {"status": "success", "data": [1, 2, 3]}
```

## 📚 Documentation

This documentation is organized into two main sections:

*   **[User Guide](getting-started.md)**: Step-by-step guides to help you learn how to use JsWeb, from installation to deployment.
*   **[API Reference](cli.md)**: Detailed reference documentation for the JsWeb API and CLI.

## 🤝 Contributing

JsWeb is an open-source project, and we welcome contributions from the community! Whether you want to fix a bug, add a feature, or improve the documentation, your help is appreciated.

Check out our [GitHub repository](https://github.com/Jsweb-Tech/jsweb) to get started.

## 📄 License

This project is licensed under the terms of the MIT license.

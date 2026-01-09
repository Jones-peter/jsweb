<p align="center">
<a href="https://jsweb-framework.site/" target="_blank">
  <img src="https://github.com/Jones-peter/jsweb/blob/main/images/jsweb-main-logo.png?raw=true" alt="JsWeb Logo" width="300">
</a>
</p>

<p align="center" style="font-size: 1.2em; font-weight: 500; margin: 1em 0;">
  <strong>The Blazing-Fast ASGI Lightweight Python Web Framework</strong>
</p>

<p align="center">
  Build full-stack web apps and APIs with JsWeb. Pure Python, pure speed.
</p>

<p align="center">
  <a href="https://pypi.org/project/jsweb/">
    <img src="https://img.shields.io/pypi/v/jsweb" alt="PyPI version"/>
  </a>
  <img src="https://img.shields.io/badge/license-MIT-red.svg" alt="License"/>
  <a href="https://pepy.tech/project/Jsweb">
    <img src="https://static.pepy.tech/personalized-badge/jsweb?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLUE&right_color=GREEN&left_text=downloads" alt="Downloads"/>
  </a>
</p>

<p align="center">
  <a href="https://discord.gg/cqg5wgEVhP">
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

---
## 🏆 Contributors

<a href="https://github.com/jones-peter/jsweb/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Jsweb-Tech/jsweb" alt="Contributors" />
</a>

---

## About JsWeb

**JsWeb** is a modern, high-performance Python web framework built from the ground up on the **ASGI** standard. It's designed for developers who want the speed of asynchronous programming with the simplicity of a classic framework.
With built-in, zero-configuration AJAX and a focus on developer experience, JsWeb makes it easy to build fast, dynamic web applications without writing a single line of JavaScript.

### Why Choose JsWeb?

- ⚡ **Lightning Fast** - ASGI-based async framework handles thousands of concurrent connections
- 🎯 **Developer Experience** - Simple, intuitive API inspired by Flask with modern features
- 🚀 **Full-Stack Ready** - Everything you need: routing, forms, templates, database, admin panel
- 🔄 **Zero-Config AJAX** - Automatic SPA-like experience without JavaScript
- 🛡️ **Security First** - CSRF protection, secure sessions, password hashing built-in
- 📦 **Production Ready** - Auto-generated admin panel, API docs, and more

---

## ✨ Core Features

- **🚀 Blazing-Fast ASGI Core** - Built for speed and concurrency, compatible with servers like Uvicorn
- **🔄 Zero-Config AJAX** - Forms and navigation automatically handled for a smooth SPA feel
- **🛣️ Elegant Routing** - Simple decorator-based route definition
- **🎨 Jinja2 Templating** - Powerful templating engine with inheritance and macros
- **🛡️ Built-in Security** - CSRF protection, password hashing, and secure session management
- **📝 Full-Featured Forms** - Form validation, file uploads, and field types
- **🗄️ SQLAlchemy Integration** - ORM with Alembic migrations included
- **⚙️ Automatic Admin Panel** - Production-ready data management interface generated automatically
- **🧩 Modular Blueprints** - Organize code into clean, reusable components
- **🛠️ Powerful CLI** - Create projects, run server, and manage database from command line
- **📚 Auto API Documentation** - OpenAPI 3.0.3 docs at `/docs`, `/redoc`, and `/openapi.json`
- **🔐 Hybrid DTO System** - Uses Pydantic v2 internally with clean JsWeb API

---

## 🚀 Quick Start (30 seconds)

### 1. Install JsWeb

```bash
pip install jsweb
```

### 2. Create a Project

```bash
jsweb new my_project
cd my_project
```

### 3. Run the Server

```bash
jsweb run --reload
```

Visit **http://127.0.0.1:8000** and your app is live! 🎉

---

## 📝 Basic Example

Here's a simple but complete JsWeb application:

**`views.py`** - Define your routes
```python
from jsweb import Blueprint, render

views_bp = Blueprint('views')

@views_bp.route("/")
async def home(req):
    return render(req, "welcome.html", {"name": "World"})

@views_bp.route("/api/status")
async def status(req):
    return {"status": "online", "message": "Hello from JsWeb!"}
```

**`app.py`** - Wire it all together
```python
from jsweb import JsWebApp
from views import views_bp
import config

app = JsWebApp(config=config)
app.register_blueprint(views_bp)

# Run with: jsweb run --reload
```

That's all you need for a working application!

---

## 📖 Installation & Setup

Get up and running in under a minute.

### Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **pip** (Python package manager)
- A text editor or IDE

### Step 1: Create Virtual Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install JsWeb

```bash
pip install jsweb
```

### Step 3: Create New Project

```bash
jsweb new my_awesome_app
cd my_awesome_app
```

### Step 4: Setup Database (Optional)

```bash
jsweb db prepare -m "Initial migration"
jsweb db upgrade
```

### Step 5: Run Development Server

```bash
jsweb run --reload
```

Visit `http://127.0.0.1:8000` - your app is running! 🎉

---

## 🛠️ Command-Line Interface (CLI)

JsWeb includes powerful CLI tools to streamline development:

### `jsweb run` - Start Server

```bash
jsweb run --reload              # Auto-reload on changes
jsweb run --host 0.0.0.0        # Accessible from network
jsweb run --port 5000           # Custom port
jsweb run --reload --qr         # QR code for mobile access
```

### `jsweb new` - Create Project

```bash
jsweb new my_project            # Create new project with boilerplate
cd my_project
```

### `jsweb db` - Database Management

```bash
jsweb db prepare -m "Message"   # Generate migration
jsweb db upgrade                # Apply migrations
jsweb db downgrade              # Revert last migration
```

### `jsweb create-admin` - Admin User

```bash
jsweb create-admin              # Interactive admin user creation
```

---

## 📚 Documentation

Complete documentation available at **https://jsweb-framework.site**

### Core Guides

- **[Getting Started](https://jsweb-tech.github.io/jsweb/getting-started/)** - Installation and setup
- **[Routing](https://jsweb-tech.github.io/jsweb/routing/)** - URL mapping and HTTP methods
- **[Templating](https://jsweb-tech.github.io/jsweb/templating/)** - Jinja2 templates and filters
- **[Database](https://jsweb-tech.github.io/jsweb/database/)** - Models, queries, and migrations
- **[Forms](https://jsweb-tech.github.io/jsweb/forms/)** - Form handling and validation
- **[Blueprints](https://jsweb-tech.github.io/jsweb/blueprints/)** - Modular application structure
- **[Admin Panel](https://jsweb-tech.github.io/jsweb/admin/)** - Data management interface
- **[Configuration](https://jsweb-tech.github.io/jsweb/configuration/)** - App settings
- **[CLI Reference](https://jsweb-tech.github.io/jsweb/cli/)** - Command-line tools
- **[OpenAPI Guide](https://jsweb-tech.github.io/jsweb/JSWEB_OPENAPI_GUIDE/)** - API documentation

---

## 🌟 Key Concepts

### Blueprints - Modular Organization

Organize your application into logical modules:

```python
from jsweb import Blueprint

# Create a blueprint
auth_bp = Blueprint('auth', url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
async def login(req):
    return render(req, 'login.html')

@auth_bp.route('/logout')
async def logout(req):
    return redirect('/')

# Register in app.py
app.register_blueprint(auth_bp)
```

### Forms with Validation

Built-in form handling with validation:

```python
from jsweb.forms import Form, StringField
from jsweb.validators import DataRequired, Email

class LoginForm(Form):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = StringField("Password", validators=[DataRequired()])

@app.route("/login", methods=["GET", "POST"])
async def login(req):
    form = LoginForm(await req.form())
    if form.validate():
        # Handle login
        pass
    return render(req, "login.html", {"form": form})
```

### Database Models

Define models with SQLAlchemy:

```python
from jsweb.database import ModelBase, Column, Integer, String

class User(ModelBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)

# Query the database
user = User.query.get(1)
users = User.query.all()
new_user = User.create(username="john", email="john@example.com")
```

### Admin Panel

Auto-generated admin interface:

```python
from jsweb.admin import Admin

admin = Admin(app)
admin.register(User)
admin.register(Post)
admin.register(Category)

# Access at http://localhost:8000/admin
```

---

## 🤝 Community & Support

- **📖 Documentation** - [jsweb-framework.site](https://jsweb-framework.site)
- **💬 Discord** - [Join community](https://discord.gg/cqg5wgEVhP)
- **🐛 Issues** - [Report bugs](https://github.com/Jsweb-Tech/jsweb/issues)
- **💡 Questions & Discussions** - [Discord Community](https://discord.gg/cqg5wgEVhP)
- **🔗 GitHub** - [Jsweb-Tech/jsweb](https://github.com/Jsweb-Tech/jsweb)

---

## 👥 Contributing

We welcome contributions from the community! Whether you want to fix a bug, add a feature, or improve documentation:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

See [Contributing Guide](CONTRIBUTING.md) for details.

---

## 📊 Project Status

- **Status**: Active Development
- **Python**: 3.8+
- **License**: MIT
- **Latest Version**: Check [PyPI](https://pypi.org/project/jsweb/)

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made and Maintained by the JsWeb team<br>
  <a href="https://discord.gg/cqg5wgEVhP" target="_blank">Join our Discord community</a> • 
  <a href="https://github.com/sponsors/Jones-peter" target="_blank">Sponsor us</a>
</p>

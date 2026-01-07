# Database

JsWeb provides a simple and powerful way to work with databases using [SQLAlchemy](https://www.sqlalchemy.org/), a popular SQL toolkit and Object-Relational Mapper (ORM).

## Table of Contents

- [Configuration](#configuration)
- [Defining Models](#defining-models)
- [Model Fields](#model-fields)
- [Return Types](#return-types)
- [Querying the Database](#querying-the-database)
- [Database Migrations](#database-migrations)
- [Relationships](#relationships)
- [Advanced Queries](#advanced-queries)
- [Best Practices](#best-practices)

## Configuration

To get started, you need to configure your database connection in your `config.py` file.

```python
# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "app.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### Supported Databases

| Database | Connection String Example |
|----------|---------------------------|
| SQLite | `sqlite:///app.db` |
| PostgreSQL | `postgresql://user:password@localhost/dbname` |
| MySQL | `mysql://user:password@localhost/dbname` |
| MariaDB | `mariadb://user:password@localhost/dbname` |

!!! tip "SQLite for Development"
    SQLite is perfect for development and small projects. For production, use PostgreSQL or MySQL.

## Defining Models

Models are Python classes that represent the tables in your database. You can define your models in the `models.py` file by inheriting from `jsweb.database.ModelBase`.

```python
# models.py
from jsweb.database import ModelBase, Column, Integer, String, DateTime, Text
from datetime import datetime

class User(ModelBase):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"
```

## Model Fields

Here are the common column types available:

| Type | Description | Example |
|------|-------------|---------|
| `Integer` | Integer numbers | `Column(Integer)` |
| `String(length)` | Short text | `Column(String(100))` |
| `Text` | Long text | `Column(Text)` |
| `Boolean` | True/False values | `Column(Boolean)` |
| `DateTime` | Date and time | `Column(DateTime, default=datetime.utcnow)` |
| `Date` | Date only | `Column(Date)` |
| `Float` | Decimal numbers | `Column(Float)` |
| `JSON` | JSON data | `Column(JSON)` |
| `Enum` | Multiple choices | `Column(Enum('admin', 'user'))` |

### Column Options

```python
class Product(ModelBase):
    __tablename__ = 'products'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Unique constraint
    sku = Column(String(50), unique=True, nullable=False)
    
    # With default value
    active = Column(Boolean, default=True)
    
    # Not null
    name = Column(String(100), nullable=False)
    
    # Indexed for faster queries
    category = Column(String(50), index=True)
```

## Return Types

ModelBase provides CRUD (Create, Read, Update, Delete) operations with the following return types:

### ModelBase Methods Return Types

| Method | Return Type | Description |
|--------|------------|-------------|
| `Model.create(**kwargs)` | `Model` | Creates and saves instance |
| `instance.save()` | `None` | Saves changes to database |
| `instance.update(**kwargs)` | `None` | Updates fields and saves |
| `instance.delete()` | `None` | Deletes instance from database |
| `Model.query.get(id)` | `Optional[Model]` | Get by primary key or None |
| `Model.query.first()` | `Optional[Model]` | Get first result or None |
| `Model.query.all()` | `List[Model]` | Get all results as list |
| `Model.query.filter_by()` | `Query` | Query builder |

### Example with Type Hints

```python
from typing import Optional, List
from jsweb.database import ModelBase

class User(ModelBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
    email = Column(String(120))

# Create - returns User instance
user: User = User.create(username="alice", email="alice@example.com")

# Read - returns Optional[User]
user: Optional[User] = User.query.get(1)
user: Optional[User] = User.query.filter_by(username="bob").first()
users: List[User] = User.query.all()

# Update - returns None
user.email = "newemail@example.com"
user.save()  # -> None

# Update with update() - returns None
user.update(email="another@example.com")  # -> None

# Delete - returns None
user.delete()  # -> None
```

## Querying the Database

### Get All Records

```python
from typing import List
from .models import User
from jsweb.response import render, HTMLResponse

@app.route("/users")
async def user_list(req) -> HTMLResponse:
    users: List[User] = User.query.all()
    return render(req, "users.html", {"users": users})
```

### Get a Single Record by ID

```python
from typing import Optional
from jsweb.response import render, json, HTMLResponse, JSONResponse

@app.route("/user/<int:user_id>")
async def user_detail(req, user_id: int) -> HTMLResponse:
    user: Optional[User] = User.query.get(user_id)
    if user is None:
        return render(req, "404.html", {}), 404
    return render(req, "user.html", {"user": user})

# JSON API version
@app.route("/api/user/<int:user_id>")
async def api_user_detail(req, user_id: int) -> JSONResponse:
    user: Optional[User] = User.query.get(user_id)
    if user is None:
        return json({"error": "User not found"}, status_code=404)
    return json(user.to_dict())
```

### Filter Records

```python
from typing import List, Optional
from sqlalchemy import or_

# Get user by username - returns Optional[User]
user: Optional[User] = User.query.filter_by(username="alice").first()

# Get all admin users - returns List[User]
admins: List[User] = User.query.filter_by(role="admin").all()

# Using filter() for more complex conditions - returns List[User]
users: List[User] = User.query.filter(
    or_(User.username == "alice", User.email == "alice@example.com")
).all()
```

!!! tip "first() vs all()"
    - `first()` returns `Optional[Model]` (first result or `None`)
    - `all()` returns `List[Model]` (all results)
    - `get(id)` returns `Optional[Model]` (by primary key or `None`)

### Creating Records

```python
# Method 1: Using create() - returns Model instance
new_user: User = User.create(username="john", email="john@example.com")

# Method 2: Creating and saving manually - returns None
user = User(username="jane", email="jane@example.com")
user.save()  # -> None
```

### Updating Records

```python
# Method 1: Manual update - returns None
user: Optional[User] = User.query.get(1)
if user:
    user.email = "newemail@example.com"
    user.save()  # -> None

# Method 2: Using update() - returns None
user.update(email="another@example.com")  # -> None
```

### Deleting Records

```python
# Method 1: Delete instance - returns None
user: Optional[User] = User.query.get(1)
if user:
    user.delete()  # -> None

# Method 2: Query and delete
User.query.filter_by(username="inactive").delete()
```

## Database Migrations

JsWeb uses [Alembic](https://alembic.sqlalchemy.org/) to handle database migrations. Alembic allows you to track changes to your database schema and apply them in a systematic way.

### Generating a Migration

After modifying your models, generate a new migration:

```bash
jsweb db prepare -m "Create user table"
```

This creates a migration file in `alembic/versions/` that captures your schema changes.

### Applying Migrations

Apply pending migrations to your database:

```bash
jsweb db upgrade
```

### Reverting Migrations

Undo the last migration:

```bash
jsweb db downgrade
```

!!! warning "Production Migrations"
    Always test migrations in a development environment before running them in production.

## Relationships

Create relationships between models for more complex data structures.

### One-to-Many Relationship

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Author(ModelBase):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    
    # Relationship: one author has many books
    books = relationship("Book", back_populates="author")

class Book(ModelBase):
    __tablename__ = 'books'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    
    # Relationship: many books belong to one author
    author = relationship("Author", back_populates="books")
```

### Accessing Related Data

```python
# Get author and their books
author = Author.query.get(1)
print(author.books)  # List of all books by this author

# Get book and its author
book = Book.query.get(1)
print(book.author.name)  # Name of the book's author
```

## Advanced Queries

### Counting Records

```python
total_users = User.query.count()
admin_count = User.query.filter_by(role="admin").count()
```

### Ordering Results

```python
# Order by name (ascending)
users = User.query.order_by(User.username).all()

# Order by created_at (descending)
from sqlalchemy import desc
users = User.query.order_by(desc(User.created_at)).all()
```

### Pagination

```python
page = 1
per_page = 10
users = User.query.paginate(page=page, per_page=per_page)
```

### Limiting Results

```python
# Get first 5 users
users = User.query.limit(5).all()

# Skip 10, then get 5
users = User.query.offset(10).limit(5).all()
```

## Best Practices

!!! tip "Always Use Transactions"
    Use transactions for operations that modify multiple records:
    
    ```python
    try:
        user = User.create(username="alice", email="alice@example.com")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise
    ```

!!! warning "N+1 Query Problem"
    Avoid fetching related data in loops. Use eager loading:
    
    ```python
    # Bad: N queries
    books = Book.query.all()
    for book in books:
        print(book.author.name)  # Separate query for each book
    
    # Good: 2 queries
    from sqlalchemy.orm import joinedload
    books = Book.query.options(joinedload(Book.author)).all()
    ```

!!! info "Indexes for Performance"
    Add indexes to frequently queried columns:
    
    ```python
    class User(ModelBase):
        __tablename__ = 'users'
        email = Column(String(120), unique=True, index=True)
        username = Column(String(80), index=True)
    ```

!!! note "Migration Naming"
    Use descriptive migration messages:
    
    ```bash
    jsweb db prepare -m "Add email verification status to users"
    jsweb db prepare -m "Create products and categories tables"
    ```


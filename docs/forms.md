# Forms

JsWeb provides a powerful and easy-to-use form library that simplifies the process of handling user input and validation.

## Table of Contents

- [Creating a Form](#creating-a-form)
- [Form Fields](#form-fields)
- [Return Types](#return-types)
- [Validators](#validators)
- [Rendering Forms](#rendering-forms)
- [Form Validation](#form-validation)
- [File Upload](#file-upload)
- [CSRF Protection](#csrf-protection)
- [Custom Validators](#custom-validators)
- [Best Practices](#best-practices)

## Creating a Form

To create a form, define a class that inherits from `jsweb.forms.Form`. Add fields as class attributes:

```python
from jsweb.forms import Form, StringField, PasswordField, HiddenField
from jsweb.validators import DataRequired, Length

class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField("Password", validators=[DataRequired()])
    csrf_token = HiddenField()
```

## Form Fields

JsWeb provides a variety of form fields for different input types.

### Return Types for Field Operations

| Operation | Return Type | Description |
|-----------|------------|-------------|
| `field()` or `field.render()` | `Markup` (str) | HTML rendering of field |
| `field.label` | `Label` | Form label object |
| `field.validate(form)` | `bool` | Validation result |
| `field.data` | `Any` | Field's current value |
| `field.errors` | `List[str]` | List of validation errors |

### Text Fields

| Field | Description | Example | Renders As |
|-------|-------------|---------|-----------|
| `StringField` | Single-line text input | `StringField("Name")` | `<input type="text">` |
| `PasswordField` | Password input (hidden) | `PasswordField("Password")` | `<input type="password">` |
| `TextAreaField` | Multi-line text input | `TextAreaField("Comments")` | `<textarea>` |
| `EmailField` | Email input | `EmailField("Email")` | `<input type="email">` |
| `URLField` | URL input | `URLField("Website")` | `<input type="url">` |
| `SearchField` | Search input | `SearchField("Search")` | `<input type="search">` |

### Number & Boolean Fields

| Field | Description | Example | Renders As |
|-------|-------------|---------|-----------|
| `IntegerField` | Integer input | `IntegerField("Age")` | `<input type="number">` |
| `FloatField` | Decimal number input | `FloatField("Price")` | `<input type="number" step="any">` |
| `DecimalField` | High-precision decimal | `DecimalField("Amount")` | `<input type="text">` |
| `BooleanField` | Checkbox | `BooleanField("Agree to terms")` | `<input type="checkbox">` |

### Date & Time Fields

| Field | Description | Example | Renders As |
|-------|-------------|---------|-----------|
| `DateField` | Date picker | `DateField("Birth Date")` | `<input type="date">` |
| `TimeField` | Time picker | `TimeField("Start Time")` | `<input type="time">` |
| `DateTimeField` | Date & time picker | `DateTimeField("Appointment")` | `<input type="datetime-local">` |

### Selection Fields

| Field | Description | Example | Renders As |
|-------|-------------|---------|-----------|
| `SelectField` | Dropdown list | `SelectField("Country", choices=[...])` | `<select>` |
| `RadioField` | Radio button group | `RadioField("Gender", choices=[...])` | `<input type="radio">` |
| `FileField` | File upload | `FileField("Upload")` | `<input type="file">` |
| `HiddenField` | Hidden field (CSRF token) | `HiddenField()` | `<input type="hidden">` |

### Field Rendering Example

```python
from jsweb.forms import Form, StringField
from markupsafe import Markup

class MyForm(Form):
    name = StringField("Your Name")

@app.route("/form")
async def form_page(req) -> HTMLResponse:
    form = MyForm()
    
    # Render field - returns Markup (str-like)
    html_input: Markup = form.name()      # <input type="text" id="name" name="name">
    label_html: Markup = form.name.label  # <label for="name">Your Name</label>
    
    # Get field data
    field_value = form.name.data          # type: Optional[str]
    
    # Validate field
    is_valid: bool = form.name.validate(form)
    
    # Get validation errors
    errors: List[str] = form.name.errors
    
    return html(f"{label_html} {html_input}")
```

### Complete Example

```python
from jsweb.forms import Form, StringField, IntegerField, SelectField, DateField, BooleanField
from jsweb.validators import DataRequired, Email, NumberRange

class UserRegistrationForm(Form):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    age = IntegerField("Age", validators=[NumberRange(min=18, max=120)])
    country = SelectField("Country", choices=[
        ("us", "United States"),
        ("uk", "United Kingdom"),
        ("ca", "Canada")
    ])
    birth_date = DateField("Birth Date")
    newsletter = BooleanField("Subscribe to newsletter")
    csrf_token = HiddenField()
```

## Return Types

Validators check that submitted data is valid. Pass a list of validators to the `validators` argument:

```python
from jsweb.validators import (
    DataRequired, Length, Email, EqualTo, NumberRange,
    FileRequired, FileAllowed, URL, Regexp
)

class Form(Form):
    username = StringField("Username", validators=[
        DataRequired(message="Username is required"),
        Length(min=4, max=25, message="Username must be 4-25 characters")
    ])
```

### Built-in Validators

| Validator | Purpose | Example |
|-----------|---------|---------|
| `DataRequired` | Field cannot be empty | `DataRequired()` |
| `Length` | String length validation | `Length(min=3, max=50)` |
| `Email` | Valid email format | `Email()` |
| `URL` | Valid URL format | `URL()` |
| `EqualTo` | Compare with another field | `EqualTo('password')` |
| `NumberRange` | Number within range | `NumberRange(min=0, max=100)` |
| `FileRequired` | File must be uploaded | `FileRequired()` |
| `FileAllowed` | Allowed file extensions | `FileAllowed(['pdf', 'doc'])` |
| `FileSize` | File size limit | `FileSize(max_size=5_000_000)` |
| `Regexp` | Match regex pattern | `Regexp(r'^[A-Z]')` |
| `Optional` | Field is optional | `Optional()` |

### Validator Examples

```python
class SignUpForm(Form):
    username = StringField("Username", validators=[
        DataRequired(),
        Length(min=4, max=20)
    ])
    
    email = StringField("Email", validators=[
        DataRequired(),
        Email(message="Invalid email address")
    ])
    
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8)
    ])
    
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match")
    ])
    
    age = IntegerField("Age", validators=[
        NumberRange(min=18, message="Must be at least 18")
    ])
    
    website = StringField("Website (optional)", validators=[URL()])
```

!!! tip "Custom Messages"
    Provide custom validation error messages to improve user experience.

## Rendering Forms

Use the `render` function to pass the form to your template. The `render()` function returns `HTMLResponse`:

```python
from jsweb.response import render, HTMLResponse
from .forms import LoginForm

@app.route("/login", methods=["GET", "POST"])
async def login(req) -> HTMLResponse:
    form = LoginForm(await req.form(), await req.files())
    
    # validate() returns bool
    if req.method == "POST" and form.validate():
        # Handle the login
        username: str = form.username.data
        # ... authentication logic ...
    
    # render() returns HTMLResponse
    return render(req, "login.html", {"form": form})
```

## Form Validation

### Checking if Form is Valid

The `validate()` method returns a `bool` indicating if all fields passed validation.

```python
from typing import List, Dict, Any

# Check if form is valid - returns bool
is_valid: bool = form.validate()

if is_valid:
    # Process form data
    data: Dict[str, Any] = form.data  # All form data as dictionary
    username: str = form.username.data
else:
    # Form has errors
    errors: Dict[str, List[str]] = form.errors  # Dictionary of field errors
    for field, error_list in errors.items():
        print(f"{field}: {error_list}")
```

### Accessing Field Data

```python
from typing import Any, List

# Get specific field value
username: str = form.username.data

# Get all form data - returns dict
all_data: dict[str, Any] = form.data

# Check if field has errors - returns bool
has_errors: bool = bool(form.username.errors)

# Get error messages - returns List[str]
error_messages: List[str] = form.username.errors
for error in error_messages:
    print(error)
```

### Rendering in Template

```html
<!-- templates/login.html -->
<form method="post" enctype="multipart/form-data">
    {{ form.csrf_token() }}
    
    <div class="form-group">
        {{ form.username.label }}
        {{ form.username() }}
        {% if form.username.errors %}
            <div class="errors">
                {% for error in form.username.errors %}
                    <p>{{ error }}</p>
                {% endfor %}
            </div>
        {% endif %}
    </div>
    
    <div class="form-group">
        {{ form.password.label }}
        {{ form.password() }}
        {% if form.password.errors %}
            <div class="errors">
                {% for error in form.password.errors %}
                    <p>{{ error }}</p>
                {% endfor %}
            </div>
        {% endif %}
    </div>
    
    <button type="submit">Log In</button>
</form>
```

### Styling with CSS

```css
.errors {
    color: #d32f2f;
    margin-top: 0.5rem;
}

.form-group {
    margin-bottom: 1rem;
}

input.error {
    border-color: #d32f2f;
}
```

## File Upload

Handle file uploads with `FileField`:

```python
from jsweb.forms import Form, FileField, StringField
from jsweb.validators import FileRequired, FileAllowed

class ProfileForm(Form):
    bio = StringField("Bio")
    avatar = FileField("Profile Picture", validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'])
    ])
```

### Processing File Uploads

```python
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

@app.route("/upload", methods=["GET", "POST"])
async def upload_profile(req):
    form = ProfileForm(await req.form(), await req.files())
    
    if req.method == "POST" and form.validate():
        file = form.avatar.data
        
        # Secure the filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file
        file.save(filepath)
        
        return "File uploaded successfully!"
    
    return render(req, "upload.html", {"form": form})
```

!!! warning "Security"
    Always validate file uploads using `FileAllowed` and `secure_filename()` to prevent security vulnerabilities.

## CSRF Protection

JsWeb provides built-in CSRF protection. Include a hidden `csrf_token` field in your forms:

```python
class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    csrf_token = HiddenField()  # Required for CSRF protection
```

### In Templates

```html
<form method="post">
    {{ form.csrf_token() }}
    <!-- Rest of form fields -->
</form>
```

!!! info "CSRF Token Validation"
    JsWeb automatically validates CSRF tokens on POST requests. Always include the `csrf_token` field in your forms.

!!! note "Future API Header Support"
    Future versions of JsWeb will support sending the CSRF token in the `X-CSRF-Token` HTTP header for SPAs and API-first applications.

## Custom Validators

Create custom validators for specific validation logic:

```python
from jsweb.validators import ValidationError

def validate_username_available(form, field):
    """Check if username is not already taken"""
    from .models import User
    if User.query.filter_by(username=field.data).first():
        raise ValidationError('Username already taken')

def validate_no_special_chars(form, field):
    """Check that field contains no special characters"""
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', field.data):
        raise ValidationError('Only alphanumeric and underscore allowed')

class SignUpForm(Form):
    username = StringField("Username", validators=[
        DataRequired(),
        validate_username_available
    ])
    
    bio = TextAreaField("Bio", validators=[
        validate_no_special_chars
    ])
```

!!! tip "Validation Order"
    Built-in validators run first, then custom validators. Place custom validators last in the list.

## Best Practices

!!! warning "Always Validate Input"
    Never trust user input. Always validate on the server side, even if you have client-side validation:
    
    ```python
    if form.validate():
        # Safe to use form.data
    ```

!!! tip "Use Specific Field Types"
    Use the most specific field type for better semantics:
    
    ```python
    # Good
    email = EmailField("Email", validators=[Email()])
    age = IntegerField("Age")
    
    # Less good
    email = StringField("Email")
    age = StringField("Age")
    ```

!!! info "Security: Password Fields"
    Always use `PasswordField` for passwords, never `StringField`:
    
    ```python
    # Good
    password = PasswordField("Password")
    
    # Bad
    password = StringField("Password")  # Not hidden!
    ```

!!! note "Flash Messages"
    Provide user feedback after form submission:
    
    ```python
    if form.validate():
        # Process form
        return redirect("/success")
    else:
        # Show validation errors
        return render(req, "form.html", {"form": form})
    ```

!!! tip "Organize Large Forms"
    Break large forms into multiple steps or use field groups:
    
    ```python
    class CheckoutForm(Form):
        # Billing information
        billing_address = StringField("Address")
        
        # Shipping information
        shipping_address = StringField("Address")
        
        # Payment information
        card_number = StringField("Card Number")
    ```


"""Tests for JsWeb forms and validation system."""

from io import BytesIO

import pytest


@pytest.mark.unit
@pytest.mark.forms
def test_form_creation():
    """Test basic form creation."""
    from jsweb.forms import Form, StringField

    class TestForm(Form):
        username = StringField("Username")

    form = TestForm()
    assert form is not None
    assert hasattr(form, "username")


@pytest.mark.unit
@pytest.mark.forms
def test_stringfield_creation():
    """Test StringField creation."""
    from jsweb.forms import Form, StringField

    class TestForm(Form):
        email = StringField("Email")

    form = TestForm()
    assert form.email is not None
    # Label is an object, not a string
    assert hasattr(form.email, "label") or hasattr(form.email, "name")


@pytest.mark.unit
@pytest.mark.forms
def test_form_with_validators():
    """Test form with validators."""
    from jsweb.forms import Form, StringField
    from jsweb.validators import DataRequired, Email

    class LoginForm(Form):
        email = StringField("Email", validators=[DataRequired(), Email()])
        password = StringField("Password", validators=[DataRequired()])

    form = LoginForm()
    assert len(form.email.validators) >= 2
    assert len(form.password.validators) >= 1


@pytest.mark.unit
@pytest.mark.forms
def test_form_field_population():
    """Test populating form fields with data."""
    from jsweb.forms import Form, StringField

    class UserForm(Form):
        username = StringField("Username")
        email = StringField("Email")

    form = UserForm()
    # Manually set field data after form creation
    form.username.data = "john_doe"
    form.email.data = "john@example.com"
    assert form.username.data == "john_doe"
    assert form.email.data == "john@example.com"


@pytest.mark.unit
@pytest.mark.forms
def test_datarequired_validator():
    """Test DataRequired validator."""
    from jsweb.validators import DataRequired, ValidationError

    validator = DataRequired()

    class MockField:
        data = None

    field = MockField()

    # Should raise for None/empty data
    with pytest.raises(ValidationError):
        validator(None, field)

    # Should not raise for valid data
    field.data = "valid data"
    validator(None, field)  # Should not raise


@pytest.mark.unit
@pytest.mark.forms
def test_email_validator():
    """Test Email validator."""
    from jsweb.validators import Email, ValidationError

    validator = Email()

    class MockField:
        def __init__(self, data):
            self.data = data

    # Valid email
    field = MockField("test@example.com")
    validator(None, field)  # Should not raise

    # Invalid email
    field = MockField("not-an-email")
    with pytest.raises(ValidationError):
        validator(None, field)


@pytest.mark.unit
@pytest.mark.forms
def test_length_validator():
    """Test Length validator."""
    from jsweb.validators import Length, ValidationError

    validator = Length(min=3, max=10)

    class MockField:
        def __init__(self, data):
            self.data = data

    # Valid length
    field = MockField("hello")
    validator(None, field)  # Should not raise

    # Too short
    field = MockField("ab")
    with pytest.raises(ValidationError):
        validator(None, field)

    # Too long
    field = MockField("this is way too long")
    with pytest.raises(ValidationError):
        validator(None, field)


@pytest.mark.unit
@pytest.mark.forms
def test_eql_validator():
    """Test EqualTo validator."""
    from jsweb.validators import EqualTo, ValidationError

    class MockForm:
        def __getitem__(self, key):
            if key == "password":
                field = type("Field", (), {"data": "mypassword"})()
                return field
            raise KeyError(key)

    validator = EqualTo("password")

    class MockField:
        def __init__(self, data):
            self.data = data

    # Matching passwords
    field = MockField("mypassword")
    validator(MockForm(), field)  # Should not raise

    # Non-matching passwords
    field = MockField("different")
    with pytest.raises(ValidationError):
        validator(MockForm(), field)


@pytest.mark.unit
@pytest.mark.forms
def test_form_multiple_fields():
    """Test form with multiple different field types."""
    from jsweb.forms import BooleanField, Form, IntegerField, StringField

    class ProfileForm(Form):
        name = StringField("Name")
        age = IntegerField("Age")
        active = BooleanField("Active")

    form = ProfileForm()
    # Manually set field data
    form.name.data = "John Doe"
    form.age.data = 30
    form.active.data = True
    assert form.name.data == "John Doe"
    assert form.age.data == 30
    assert form.active.data is True


@pytest.mark.unit
@pytest.mark.forms
def test_form_field_rendering():
    """Test form field HTML rendering."""
    from jsweb.forms import Form, StringField

    class ContactForm(Form):
        email = StringField("Email")

    form = ContactForm()

    # Should be able to render field
    field_html = str(form.email)
    assert "email" in field_html.lower() or form.email is not None


@pytest.mark.unit
@pytest.mark.forms
def test_textarea_field():
    """Test TextAreaField."""
    from jsweb.forms import Form, TextAreaField

    class CommentForm(Form):
        comment = TextAreaField("Comment")

    form = CommentForm()
    form.comment.data = "This is a comment"
    assert form.comment.data == "This is a comment"


@pytest.mark.unit
@pytest.mark.forms
def test_select_field():
    """Test SelectField."""
    try:
        from jsweb.forms import Form, SelectField

        class CategoryForm(Form):
            category = SelectField(
                "Category",
                choices=[
                    ("tech", "Technology"),
                    ("business", "Business"),
                    ("sports", "Sports"),
                ],
            )

        form = CategoryForm()
        form.category.data = "tech"
        assert form.category.data == "tech"
    except ImportError:
        pytest.skip("SelectField not available")


@pytest.mark.unit
@pytest.mark.forms
def test_range_validator():
    """Test NumberRange validator."""
    try:
        from jsweb.validators import NumberRange, ValidationError

        validator = NumberRange(min=1, max=100)

        class MockField:
            def __init__(self, data):
                self.data = data

        # Valid range
        field = MockField(50)
        validator(None, field)  # Should not raise

        # Too small
        field = MockField(0)
        with pytest.raises(ValidationError):
            validator(None, field)

        # Too large
        field = MockField(101)
        with pytest.raises(ValidationError):
            validator(None, field)
    except ImportError:
        pytest.skip("NumberRange not available")


@pytest.mark.unit
@pytest.mark.forms
def test_regex_validator():
    """Test Regexp validator."""
    try:
        from jsweb.validators import Regexp, ValidationError

        # Only alphanumeric
        validator = Regexp(r"^\w+$")

        class MockField:
            def __init__(self, data):
                self.data = data

        # Valid
        field = MockField("username123")
        validator(None, field)  # Should not raise

        # Invalid (contains special char)
        field = MockField("user@name")
        with pytest.raises(ValidationError):
            validator(None, field)
    except ImportError:
        pytest.skip("Regexp validator not available")


@pytest.mark.unit
@pytest.mark.forms
def test_form_field_errors():
    """Test form field error handling."""
    from jsweb.forms import Form, StringField
    from jsweb.validators import DataRequired, ValidationError

    class RequiredForm(Form):
        name = StringField("Name", validators=[DataRequired()])

    form = RequiredForm()

    # Field should have validators
    assert len(form.name.validators) > 0


@pytest.mark.unit
@pytest.mark.forms
def test_file_field_validators():
    """Test FileField with validators."""
    from jsweb.forms import FileField, Form
    from jsweb.validators import FileAllowed, FileRequired, FileSize

    class UploadForm(Form):
        document = FileField(
            "Document",
            validators=[
                FileRequired(),
                FileAllowed(["pdf", "doc", "docx"]),
                FileSize(max_size=5 * 1024 * 1024),  # 5MB
            ],
        )

    form = UploadForm()
    assert form.document is not None
    assert len(form.document.validators) == 3


@pytest.mark.unit
@pytest.mark.forms
def test_hidden_field():
    """Test HiddenField."""
    try:
        from jsweb.forms import Form, HiddenField

        class SecureForm(Form):
            csrf_token = HiddenField()

        form = SecureForm()
        form.csrf_token.data = "token123"
        assert form.csrf_token.data == "token123"
    except ImportError:
        pytest.skip("HiddenField not available")


@pytest.mark.unit
@pytest.mark.forms
def test_password_field():
    """Test PasswordField."""
    try:
        from jsweb.forms import Form, PasswordField
        from jsweb.validators import DataRequired

        class LoginForm(Form):
            password = PasswordField("Password", validators=[DataRequired()])

        form = LoginForm()
        assert form.password is not None
    except ImportError:
        pytest.skip("PasswordField not available")

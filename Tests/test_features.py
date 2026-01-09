"""Tests for new JsWeb features (JSON parsing, file uploads, validators)."""

import json
import pytest
from io import BytesIO


@pytest.mark.unit
def test_import_new_features():
    """Test that all new features can be imported."""
    from jsweb import UploadedFile, FileField, FileRequired, FileAllowed, FileSize
    
    assert UploadedFile is not None
    assert FileField is not None
    assert FileRequired is not None
    assert FileAllowed is not None
    assert FileSize is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_json_request_parsing():
    """Test JSON request body parsing."""
    from jsweb.request import Request

    class FakeApp:
        class config:
            pass

    body = json.dumps({'name': 'Alice', 'email': 'alice@example.com'})
    content = body.encode('utf-8')

    app = FakeApp()
    scope = {
        'type': 'http',
        'method': 'POST',
        'path': '/',
        'query_string': b'',
        'headers': [(b'content-type', b'application/json')],
    }
    
    async def receive():
        return {'body': content, 'more_body': False}

    req = Request(scope, receive, app)
    data = await req.json()

    assert data == {'name': 'Alice', 'email': 'alice@example.com'}
    assert data['name'] == 'Alice'
    assert data['email'] == 'alice@example.com'


@pytest.mark.unit
@pytest.mark.asyncio
async def test_json_parsing_with_numbers():
    """Test JSON parsing with various data types."""
    from jsweb.request import Request

    class FakeApp:
        class config:
            pass

    body = json.dumps({'count': 42, 'active': True, 'items': [1, 2, 3]})
    content = body.encode('utf-8')

    app = FakeApp()
    scope = {
        'type': 'http',
        'method': 'POST',
        'path': '/',
        'query_string': b'',
        'headers': [(b'content-type', b'application/json')],
    }
    
    async def receive():
        return {'body': content, 'more_body': False}

    req = Request(scope, receive, app)
    data = await req.json()

    assert data['count'] == 42
    assert data['active'] is True
    assert data['items'] == [1, 2, 3]


@pytest.mark.unit
def test_filefield_creation():
    """Test FileField creation in forms."""
    from jsweb.forms import Form, FileField
    from jsweb.validators import FileRequired, FileAllowed, FileSize

    class TestForm(Form):
        upload = FileField('Upload File', validators=[
            FileRequired(),
            FileAllowed(['jpg', 'png']),
            FileSize(max_size=1024*1024)  # 1MB
        ])

    form = TestForm()
    assert form is not None
    assert hasattr(form, 'upload')
    assert len(form.upload.validators) == 3
    validator_names = [v.__class__.__name__ for v in form.upload.validators]
    assert 'FileRequired' in validator_names
    assert 'FileAllowed' in validator_names
    assert 'FileSize' in validator_names


@pytest.mark.unit
def test_fileallowed_validator_accepts_valid_extensions():
    """Test that FileAllowed validator accepts valid file extensions."""
    from jsweb.validators import FileAllowed

    class MockFile:
        def __init__(self, filename):
            self.filename = filename

    class MockField:
        def __init__(self, filename):
            self.data = MockFile(filename)

    validator = FileAllowed(['jpg', 'png', 'gif'])
    
    # Should not raise for valid extensions
    field = MockField('test.jpg')
    validator(None, field)  # Should not raise
    
    field = MockField('image.png')
    validator(None, field)  # Should not raise


@pytest.mark.unit
def test_fileallowed_validator_rejects_invalid_extensions():
    """Test that FileAllowed validator rejects invalid file extensions."""
    from jsweb.validators import FileAllowed, ValidationError

    class MockFile:
        def __init__(self, filename):
            self.filename = filename

    class MockField:
        def __init__(self, filename):
            self.data = MockFile(filename)

    validator = FileAllowed(['jpg', 'png'])
    field = MockField('script.exe')
    
    with pytest.raises(ValidationError):
        validator(None, field)


@pytest.mark.unit
def test_filesize_validator_accepts_small_files():
    """Test that FileSize validator accepts files within size limit."""
    from jsweb.validators import FileSize

    class MockFile:
        def __init__(self, size):
            self.size = size

    class MockField:
        def __init__(self, size):
            self.data = MockFile(size)

    validator = FileSize(max_size=1000)
    
    # Should not raise for small files
    field = MockField(500)
    validator(None, field)  # Should not raise
    
    field = MockField(1000)  # Exactly at limit
    validator(None, field)  # Should not raise


@pytest.mark.unit
def test_filesize_validator_rejects_large_files():
    """Test that FileSize validator rejects files exceeding size limit."""
    from jsweb.validators import FileSize, ValidationError

    class MockFile:
        def __init__(self, size):
            self.size = size

    class MockField:
        def __init__(self, size):
            self.data = MockFile(size)

    validator = FileSize(max_size=1000)
    field = MockField(2000)
    
    with pytest.raises(ValidationError):
        validator(None, field)


@pytest.mark.unit
def test_filerequired_validator():
    """Test FileRequired validator."""
    from jsweb.validators import FileRequired, ValidationError

    class MockField:
        def __init__(self, data):
            self.data = data

    validator = FileRequired()
    
    # Should raise when no file provided
    field = MockField(None)
    with pytest.raises(ValidationError):
        validator(None, field)
    
    # Should not raise when file provided
    field = MockField("dummy_file")
    validator(None, field)  # Should not raise

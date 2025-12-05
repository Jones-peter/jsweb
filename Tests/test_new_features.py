#!/usr/bin/env python
"""Test script for new JSON and file upload features."""

import json
from io import BytesIO

print("=" * 60)
print("Testing New JsWeb Features")
print("=" * 60)

# Test 1: Import all new features
print("\n[1] Testing imports...")
try:
    from jsweb import UploadedFile, FileField, FileRequired, FileAllowed, FileSize
    print("    [PASS] All new features imported successfully")
except Exception as e:
    print(f"    [FAIL] Import error: {e}")
    exit(1)

# Test 2: JSON parsing
print("\n[2] Testing JSON request body parsing...")
try:
    from jsweb.request import Request

    class FakeApp:
        class config:
            pass

    body = json.dumps({'name': 'Alice', 'email': 'alice@example.com'})
    content = body.encode('utf-8')

    app = FakeApp()
    environ = {
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': str(len(content)),
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'HTTP_COOKIE': '',
        'wsgi.input': BytesIO(content)
    }

    req = Request(environ, app)
    data = req.json

    assert data == {'name': 'Alice', 'email': 'alice@example.com'}, "JSON data mismatch"
    print(f"    [PASS] JSON parsed correctly: {data}")
except Exception as e:
    print(f"    [FAIL] JSON parsing error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: FileField in forms
print("\n[3] Testing FileField...")
try:
    from jsweb.forms import Form, FileField
    from jsweb.validators import FileRequired, FileAllowed, FileSize

    class TestForm(Form):
        upload = FileField('Upload File', validators=[
            FileRequired(),
            FileAllowed(['jpg', 'png']),
            FileSize(max_size=1024*1024)  # 1MB
        ])

    form = TestForm()
    print("    [PASS] FileField created successfully")
    print(f"    Validators: {[v.__class__.__name__ for v in form.upload.validators]}")
except Exception as e:
    print(f"    [FAIL] FileField error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: File validators
print("\n[4] Testing file validators...")
try:
    from jsweb.validators import FileAllowed, FileSize, ValidationError

    # Test FileAllowed
    class MockField:
        def __init__(self, filename):
            self.data = type('obj', (object,), {'filename': filename})()

    validator = FileAllowed(['jpg', 'png'])
    field = MockField('test.jpg')

    try:
        validator(None, field)
        print("    [PASS] FileAllowed: .jpg accepted")
    except ValidationError:
        print("    [FAIL] FileAllowed: .jpg should be accepted")

    field = MockField('test.exe')
    try:
        validator(None, field)
        print("    [FAIL] FileAllowed: .exe should be rejected")
    except ValidationError as e:
        print(f"    [PASS] FileAllowed: .exe rejected - {e}")

    # Test FileSize
    class MockFieldWithSize:
        def __init__(self, size):
            self.data = type('obj', (object,), {'size': size})()

    validator = FileSize(max_size=1000)
    field = MockFieldWithSize(500)

    try:
        validator(None, field)
        print("    [PASS] FileSize: 500 bytes accepted (max 1000)")
    except ValidationError:
        print("    [FAIL] FileSize: 500 bytes should be accepted")

    field = MockFieldWithSize(2000)
    try:
        validator(None, field)
        print("    [FAIL] FileSize: 2000 bytes should be rejected")
    except ValidationError as e:
        print(f"    [PASS] FileSize: 2000 bytes rejected")

except Exception as e:
    print(f"    [FAIL] Validator error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
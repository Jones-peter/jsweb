import re

class ValidationError(Exception):
    """Raised when a validator fails to validate its input."""
    def __init__(self, message="Invalid input."):
        super().__init__(message)

class DataRequired:
    """Checks that the field is not empty."""
    def __init__(self, message="This field is required."):
        self.message = message

    def __call__(self, form, field):
        if not field.data or not field.data.strip():
            raise ValidationError(self.message)

class Email:
    """Checks for a valid email format."""
    def __init__(self, message="Invalid email address."):
        self.message = message
        self.regex = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    def __call__(self, form, field):
        if not self.regex.match(field.data):
            raise ValidationError(self.message)

class Length:
    """Checks that the field's length is within a specified range."""
    def __init__(self, min=-1, max=-1, message=None):
        self.min = min
        self.max = max
        self.message = message

    def __call__(self, form, field):
        length = len(field.data) if field.data else 0
        if length < self.min or (self.max != -1 and length > self.max):
            if self.message:
                message = self.message
            elif self.max == -1:
                message = f"Field must be at least {self.min} characters long."
            elif self.min == -1:
                message = f"Field cannot be longer than {self.max} characters."
            else:
                message = f"Field must be between {self.min} and {self.max} characters long."
            raise ValidationError(message)

class EqualTo:
    """Compares the values of two fields."""
    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError:
            raise ValidationError(f"Invalid field name '{self.fieldname}'.")
        if field.data != other.data:
            message = self.message
            if message is None:
                message = f"Field must be equal to {self.fieldname}."
            raise ValidationError(message)

class FileRequired:
    """Checks that a file has been uploaded."""
    def __init__(self, message="File is required."):
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            raise ValidationError(self.message)

class FileAllowed:
    """Validates that the uploaded file has an allowed extension."""
    def __init__(self, allowed_extensions, message=None):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return  # No file uploaded, let FileRequired handle it

        filename = getattr(field.data, 'filename', None)
        if not filename:
            raise ValidationError("Invalid file data.")

        # Extract file extension
        if '.' not in filename:
            ext = ''
        else:
            ext = filename.rsplit('.', 1)[1].lower()

        if ext not in self.allowed_extensions:
            message = self.message
            if message is None:
                message = f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            raise ValidationError(message)

class FileSize:
    """Validates that the uploaded file size is within limits."""
    def __init__(self, max_size=None, min_size=None, message=None):
        self.max_size = max_size  # in bytes
        self.min_size = min_size  # in bytes
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return  # No file uploaded, let FileRequired handle it

        file_size = getattr(field.data, 'size', None)
        if file_size is None:
            raise ValidationError("Cannot determine file size.")

        if self.max_size is not None and file_size > self.max_size:
            message = self.message
            if message is None:
                max_mb = self.max_size / (1024 * 1024)
                message = f"File size exceeds maximum allowed size of {max_mb:.2f} MB."
            raise ValidationError(message)

        if self.min_size is not None and file_size < self.min_size:
            message = self.message
            if message is None:
                min_kb = self.min_size / 1024
                message = f"File size is below minimum required size of {min_kb:.2f} KB."
            raise ValidationError(message)

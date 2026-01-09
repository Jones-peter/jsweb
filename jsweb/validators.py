"""
This module provides a collection of standard validators for use with forms.

Each validator is a callable class that raises a `ValidationError` if the
field's data does not meet the required criteria.
"""

import re


class ValidationError(Exception):
    """Raised when a validator fails to validate its input."""

    def __init__(self, message="Invalid input."):
        super().__init__(message)


class DataRequired:
    """
    Checks that the field's data is not empty or just whitespace.

    Args:
        message (str, optional): The error message to raise if validation fails.
    """

    def __init__(self, message="This field is required."):
        self.message = message

    def __call__(self, form, field):
        """
        Performs the validation.

        Raises:
            ValidationError: If the field data is empty or contains only whitespace.
        """
        if not field.data or not field.data.strip():
            raise ValidationError(self.message)


class Email:
    """
    Checks that the field's data is a valid email address.

    Args:
        message (str, optional): The error message to raise if validation fails.
    """

    def __init__(self, message="Invalid email address."):
        self.message = message
        self.regex = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    def __call__(self, form, field):
        """
        Performs the validation using a regular expression.

        Raises:
            ValidationError: If the field data does not match the email regex.
        """
        if not self.regex.match(field.data):
            raise ValidationError(self.message)


class Length:
    """
    Checks that the length of the field's data is within a specified range.

    Args:
        min (int): The minimum required length.
        max (int): The maximum allowed length.
        message (str, optional): The error message to raise if validation fails.
    """

    def __init__(self, min=-1, max=-1, message=None):
        self.min = min
        self.max = max
        self.message = message

    def __call__(self, form, field):
        """
        Performs the validation.

        Raises:
            ValidationError: If the length is outside the specified min/max range.
        """
        length = len(field.data) if field.data else 0
        if length < self.min or (self.max != -1 and length > self.max):
            if self.message:
                message = self.message
            elif self.max == -1:
                message = f"Field must be at least {self.min} characters long."
            elif self.min == -1:
                message = f"Field cannot be longer than {self.max} characters."
            else:
                message = (
                    f"Field must be between {self.min} and {self.max} characters long."
                )
            raise ValidationError(message)


class EqualTo:
    """
    Compares the value of the field to the value of another field in the form.

    Args:
        fieldname (str): The name of the other field to compare against.
        message (str, optional): The error message to raise if validation fails.
    """

    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        """
        Performs the validation.

        Raises:
            ValidationError: If the fields' values do not match or the other field doesn't exist.
        """
        try:
            other = form[self.fieldname]
        except KeyError as err:
            raise ValidationError(f"Invalid field name '{self.fieldname}'.") from err
        if field.data != other.data:
            message = self.message
            if message is None:
                message = f"Field must be equal to {self.fieldname}."
            raise ValidationError(message)


class FileRequired:
    """
    Checks that a file has been uploaded to a file field.

    Args:
        message (str, optional): The error message to raise if validation fails.
    """

    def __init__(self, message="File is required."):
        self.message = message

    def __call__(self, form, field):
        """
        Performs the validation.

        Raises:
            ValidationError: If no file data is present in the field.
        """
        if not field.data:
            raise ValidationError(self.message)


class FileAllowed:
    """
    Validates that an uploaded file has an allowed extension.

    Args:
        allowed_extensions (list): A list of allowed file extensions (e.g., ['jpg', 'png']).
        message (str, optional): The error message to raise if validation fails.
    """

    def __init__(self, allowed_extensions, message=None):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        self.message = message

    def __call__(self, form, field):
        """
        Performs the validation.

        Raises:
            ValidationError: If the file's extension is not in the allowed list.
        """
        if not field.data:
            return

        filename = getattr(field.data, "filename", None)
        if not filename:
            raise ValidationError("Invalid file data.")

        if "." not in filename:
            ext = ""
        else:
            ext = filename.rsplit(".", 1)[1].lower()

        if ext not in self.allowed_extensions:
            message = self.message
            if message is None:
                message = f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            raise ValidationError(message)


class FileSize:
    """
    Validates that an uploaded file's size is within a specified range.

    Args:
        max_size (int, optional): The maximum allowed file size in bytes.
        min_size (int, optional): The minimum required file size in bytes.
        message (str, optional): The error message to raise if validation fails.
    """

    def __init__(self, max_size=None, min_size=None, message=None):
        self.max_size = max_size
        self.min_size = min_size
        self.message = message

    def __call__(self, form, field):
        """
        Performs the validation.

        Raises:
            ValidationError: If the file size is outside the specified min/max range.
        """
        if not field.data:
            return

        file_size = getattr(field.data, "size", None)
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
                message = (
                    f"File size is below minimum required size of {min_kb:.2f} KB."
                )
            raise ValidationError(message)

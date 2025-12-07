from .validators import ValidationError
from markupsafe import Markup

class Label:
    """A smart label that knows how to render itself."""
    def __init__(self, field_id, text):
        self.field_id = field_id
        self.text = text

    def __html__(self):
        """
        Called by Jinja2 when rendering. Returns the full HTML for the label.
        e.g., <label for="username">Username</label>
        """
        return Markup(f'<label for="{self.field_id}">{self.text}</label>')

    def __str__(self):
        return self.__html__()

class Field:
    """A single field in a form."""
    def __init__(self, label=None, validators=None, default=""):
        # The label text is stored, but the `label` property will be a Label object.
        self._label_text = label
        self.validators = validators or []
        self.data = None
        self.default = default
        self.errors = []
        self.name = None  # This will be set by the Form class

    @property
    def label(self):
        """Returns a renderable Label object."""
        return Label(self.name, self._label_text or self.name.replace('_', ' ').title())

    def validate(self, form):
        """Validate the field by running all its validators."""
        self.errors = []
        for validator in self.validators:
            try:
                validator(form, self)
            except ValidationError as e:
                self.errors.append(str(e))
        return not self.errors

    def __call__(self, **kwargs):
        """Render the field as an HTML input."""
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)
        kwargs.setdefault('type', 'text')
        if self.data:
            kwargs.setdefault('value', self.data)
        else:
            kwargs.setdefault('value', self.default)
        
        attributes = ' '.join(f'{key}="{value}"' for key, value in kwargs.items())
        # Mark the output as safe HTML for Jinja2's auto-escaping.
        return Markup(f'<input {attributes}>')

class StringField(Field):
    pass

class PasswordField(Field):
    def __call__(self, **kwargs):
        kwargs['type'] = 'password'
        return super().__call__(**kwargs)

class HiddenField(Field):
    def __call__(self, **kwargs):
        kwargs['type'] = 'hidden'
        return super().__call__(**kwargs)

class FileField(Field):
    """A field for file uploads."""
    def __init__(self, label=None, validators=None, multiple=False):
        super().__init__(label=label, validators=validators, default="")
        self.multiple = multiple

    def __call__(self, **kwargs):
        kwargs['type'] = 'file'
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)
        if self.multiple:
            kwargs['multiple'] = 'multiple'

        # Remove value attribute for file inputs (not allowed)
        kwargs.pop('value', None)

        attributes = ' '.join(f'{key}="{value}"' for key, value in kwargs.items())
        return Markup(f'<input {attributes}>')

class Form:
    """A collection of fields that can be validated together."""
    def __init__(self, formdata=None, files=None):
        self.formdata = formdata or {}
        self.files = files or {}
        self._fields = {}

        # Collect all Field instances from the class definition
        for name in dir(self):
            if isinstance(getattr(self, name), Field):
                field = getattr(self, name)
                field.name = name  # Set the field's name
                self._fields[name] = field
                # Populate field data from formdata or files if available
                if isinstance(field, FileField):
                    if name in self.files:
                        field.data = self.files[name]
                elif name in self.formdata:
                    field.data = self.formdata[name]

    def validate(self):
        """Validate all fields in the form."""
        success = True
        for name, field in self._fields.items():
            if not field.validate(self):
                success = False
        return success

    def __getitem__(self, name):
        return self._fields.get(name)

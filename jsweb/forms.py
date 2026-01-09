from .validators import ValidationError
from markupsafe import Markup


class Label:
    """A smart label that knows how to render itself."""

    def __init__(self, field_id, text):
        self.field_id = field_id
        self.text = text

    def __html__(self):
        """Renders the label as HTML."""
        return Markup(f'<label for="{self.field_id}">{self.text}</label>')

    def __str__(self):
        """Returns the HTML representation of the label."""
        return self.__html__()


class Field:
    """Base class for all form fields."""

    def __init__(self, label=None, validators=None, default=None, description=""):
        self._label_text = label
        self.validators = validators or []
        self.default = default
        self.description = description

        self.data = None
        self.errors = []
        self.name = None

    @property
    def label(self):
        """Returns a Label object for the field."""
        return Label(self.name, self._label_text or self.name.replace('_', ' ').title())

    def process_formdata(self, value):
        """Coerce the form data to the appropriate Python type."""
        self.data = value

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

        value = self.data if self.data is not None else self.default
        if value is not None:
            kwargs.setdefault('value', str(value))

        attributes = ' '.join(f'{key}="{value}"' for key, value in kwargs.items())
        return Markup(f'<input {attributes}>')


class StringField(Field):
    """A standard text input field."""
    pass


class PasswordField(Field):
    """A password input field."""

    def __call__(self, **kwargs):
        """Render the field as a password input."""
        kwargs['type'] = 'password'
        return super().__call__(**kwargs)


class HiddenField(Field):
    """A hidden input field."""

    def __call__(self, **kwargs):
        """Render the field as a hidden input."""
        kwargs['type'] = 'hidden'
        return super().__call__(**kwargs)


class IntegerField(Field):
    """A field for integer values."""

    def process_formdata(self, value):
        """Coerce the form data to an integer."""
        if value is None or value == '':
            self.data = None
            return
        try:
            self.data = int(value)
        except (ValueError, TypeError):
            self.data = None
            raise ValidationError("Not a valid integer.")

    def __call__(self, **kwargs):
        """Render the field as a number input."""
        kwargs.setdefault('type', 'number')
        return super().__call__(**kwargs)


class TextAreaField(Field):
    """A multi-line text area field."""

    def __call__(self, **kwargs):
        """Render the field as a textarea."""
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)

        value = str(self.data) if self.data is not None else str(self.default or '')
        attributes = ' '.join(f'{key}="{value}"' for key, value in kwargs.items())

        return Markup(f'<textarea {attributes}>{value}</textarea>')


class BooleanField(Field):
    """A boolean checkbox field."""

    def process_formdata(self, value):
        """Coerce the form data to a boolean."""
        self.data = True if value else False

    def __call__(self, **kwargs):
        """Render the field as a checkbox."""
        kwargs.setdefault('type', 'checkbox')
        if self.data:
            kwargs['checked'] = 'checked'
        kwargs['value'] = 'true'
        return super().__call__(**kwargs)


class SelectField(Field):
    """A select dropdown field."""

    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.choices = choices or []

    def __iter__(self):
        """Iterate over choices."""
        for value, label in self.choices:
            selected = self.data is not None and str(value) == str(self.data)
            yield (value, label, selected)

    def __call__(self, **kwargs):
        """Render the field as a select dropdown."""
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)

        attrs_str = " ".join(f'{k}="{v}"' for k, v in kwargs.items())
        html = [f'<select {attrs_str}>']
        for value, label, selected in self:
            option_attrs = {'value': value}
            if selected:
                option_attrs['selected'] = 'selected'
            option_attrs_str = " ".join(f'{k}="{v}"' for k, v in option_attrs.items())
            html.append(f'<option {option_attrs_str}>{label}</option>')
        html.append('</select>')
        return Markup(''.join(html))


class RadioField(Field):
    """A radio button field."""

    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.choices = choices or []

    def __iter__(self):
        """Iterate over choices."""
        for value, label in self.choices:
            checked = self.data is not None and str(value) == str(self.data)
            yield (value, label, checked)

    def __call__(self, **kwargs):
        """Render the field as a list of radio buttons."""
        kwargs.setdefault('id', self.name)

        html = ['<ul class="radio-list">']
        for value, label, checked in self:
            option_id = f'{self.name}-{value}'
            radio_attrs = {
                'type': 'radio',
                'name': self.name,
                'id': option_id,
                'value': value
            }
            if checked:
                radio_attrs['checked'] = 'checked'

            html.append('<li>')
            html.append(f'<input {" ".join(f"{k}=\"{v}\"" for k, v in radio_attrs.items())}>')
            html.append(f'<label for="{option_id}">{label}</label>')
            html.append('</li>')
        html.append('</ul>')
        return Markup(''.join(html))


class FileField(Field):
    """A file upload field."""

    def __init__(self, label=None, validators=None, multiple=False, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.multiple = multiple

    def process_formdata(self, value):
        """Process file data."""
        pass

    def __call__(self, **kwargs):
        """Render the field as a file input."""
        kwargs['type'] = 'file'
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)
        if self.multiple:
            kwargs['multiple'] = 'multiple'
        kwargs.pop('value', None)

        attributes = ' '.join(f'{key}="{value}"' for key, value in kwargs.items())
        return Markup(f'<input {attributes}>')


class Form:
    """A collection of fields that can be validated and rendered."""

    def __init__(self, formdata=None, files=None, **kwargs):
        self.formdata = formdata or {}
        self.files = files or {}
        self._fields = {}

        for name in dir(self):
            if isinstance(getattr(self, name), Field):
                field = getattr(self, name)
                field.name = name
                self._fields[name] = field

        for name, field in self._fields.items():
            if isinstance(field, FileField):
                field.data = self.files.get(name)
            elif name in self.formdata:
                try:
                    field.process_formdata(self.formdata.get(name))
                except ValidationError as e:
                    field.errors.append(str(e))
            else:
                field.process_formdata(None)

    def validate(self):
        """Validate all fields in the form."""
        success = True
        for name, field in self._fields.items():
            if not field.errors:
                if not field.validate(self):
                    success = False
        return success

    def __getitem__(self, name):
        """Get a field by name."""
        return self._fields.get(name)

from .validators import ValidationError
from markupsafe import Markup

class Label:
    """A smart label that knows how to render itself."""
    def __init__(self, field_id, text):
        self.field_id = field_id
        self.text = text

    def __html__(self):
        return Markup(f'<label for="{self.field_id}">{self.text}</label>')

    def __str__(self):
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
        self.name = None  # Set by the Form class

    @property
    def label(self):
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

# --- Standard Fields ---

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

class IntegerField(Field):
    def process_formdata(self, value):
        if value is None or value == '':
            self.data = None
            return
        try:
            self.data = int(value)
        except (ValueError, TypeError):
            self.data = None
            raise ValidationError("Not a valid integer.")

    def __call__(self, **kwargs):
        kwargs.setdefault('type', 'number')
        return super().__call__(**kwargs)

class TextAreaField(Field):
    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)
        
        value = str(self.data) if self.data is not None else str(self.default or '')
        attributes = ' '.join(f'{key}="{value}"' for key, value in kwargs.items())
        
        return Markup(f'<textarea {attributes}>{value}</textarea>')

class BooleanField(Field):
    def process_formdata(self, value):
        # HTML checkboxes send 'on' if checked, and nothing if not.
        self.data = True if value else False

    def __call__(self, **kwargs):
        kwargs.setdefault('type', 'checkbox')
        if self.data:
            kwargs['checked'] = 'checked'
        # The 'value' attribute for a checkbox is typically 'on' or 'true',
        # but it's the presence of the 'checked' attribute that matters.
        kwargs['value'] = 'true' 
        return super().__call__(**kwargs)

# --- Choice Fields ---

class SelectField(Field):
    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.choices = choices or []

    def __iter__(self):
        for value, label in self.choices:
            selected = self.data is not None and str(value) == str(self.data)
            yield (value, label, selected)

    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)
        
        html = [f'<select {Markup(" ".join(f"{k}=\"{v}\"" for k, v in kwargs.items()))}>']
        for value, label, selected in self:
            option_attrs = {'value': value}
            if selected:
                option_attrs['selected'] = 'selected'
            html.append(f'<option {" ".join(f"{k}=\"{v}\"" for k, v in option_attrs.items())}>{label}</option>')
        html.append('</select>')
        return Markup(''.join(html))

class RadioField(Field):
    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.choices = choices or []

    def __iter__(self):
        for value, label in self.choices:
            checked = self.data is not None and str(value) == str(self.data)
            yield (value, label, checked)

    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.name)
        
        html = ['<ul class="radio-list">']
        for value, label, checked in self:
            # Each radio button needs a unique ID
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

# --- File Field ---

class FileField(Field):
    def __init__(self, label=None, validators=None, multiple=False, **kwargs):
        super().__init__(label, validators, **kwargs)
        self.multiple = multiple

    def process_formdata(self, value):
        # File data is handled separately in the Form class
        pass

    def __call__(self, **kwargs):
        kwargs['type'] = 'file'
        kwargs.setdefault('id', self.name)
        kwargs.setdefault('name', self.name)
        if self.multiple:
            kwargs['multiple'] = 'multiple'
        kwargs.pop('value', None) # Not allowed for file inputs
        
        attributes = ' '.join(f'{key}="{value}"' for key, value in kwargs.items())
        return Markup(f'<input {attributes}>')

# --- Form Class ---

class Form:
    """A collection of fields that can be validated and rendered."""
    def __init__(self, formdata=None, files=None, **kwargs):
        self.formdata = formdata or {}
        self.files = files or {}
        self._fields = {}

        # Collect all Field instances from the class definition
        for name in dir(self):
            if isinstance(getattr(self, name), Field):
                field = getattr(self, name)
                field.name = name
                self._fields[name] = field

        # Populate data
        for name, field in self._fields.items():
            if isinstance(field, FileField):
                field.data = self.files.get(name)
            elif name in self.formdata:
                try:
                    field.process_formdata(self.formdata.get(name))
                except ValidationError as e:
                    field.errors.append(str(e))
            else:
                # For fields not in formdata (like an unchecked checkbox),
                # still run process_formdata to set a default state (e.g., False).
                field.process_formdata(None)

    def validate(self):
        """Validate all fields in the form."""
        success = True
        for name, field in self._fields.items():
            # Don't re-validate if coercion already failed
            if not field.errors:
                if not field.validate(self):
                    success = False
        return success

    def __getitem__(self, name):
        return self._fields.get(name)

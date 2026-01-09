import logging
import os

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.inspection import inspect

from jsweb import __VERSION__
from jsweb.auth import admin_required, login_user
from jsweb.blueprints import Blueprint
from jsweb.database import db_session
from jsweb.forms import Form, StringField
from jsweb.response import HTMLResponse, redirect, url_for

logger = logging.getLogger(__name__)


class Admin:
    """
    The main class for the JsWeb Admin interface.
    """

    def __init__(self, app=None):
        self.models = {}

        # --- PATHS UPDATED FOR SUB-PACKAGE ---
        # The paths are now relative to this file's location inside the 'admin' package.
        admin_dir = os.path.dirname(__file__)
        admin_template_dir = os.path.join(admin_dir, "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(admin_template_dir))

        admin_static_folder = os.path.join(admin_dir, "static")

        self.blueprint = Blueprint(
            "admin",
            url_prefix="/admin",
            static_folder=admin_static_folder,
            static_url_path="/admin/static",
        )

        if app:
            self.init_app(app)

    def render(self, request, template_name, context=None):
        """Renders a template using the admin's isolated Jinja2 environment."""
        if context is None:
            context = {}

        context["request"] = request
        context["app"] = self.app
        context["admin_models"] = self.models.keys()
        context["url_for"] = lambda endpoint, **kwargs: url_for(
            request, endpoint, **kwargs
        )
        context["library_version"] = __VERSION__

        if hasattr(request, "csrf_token"):
            context["csrf_token"] = request.csrf_token

        template = self.jinja_env.get_template(template_name)
        body = template.render(**context)
        return HTMLResponse(body)

    def init_app(self, app):
        self.app = app
        self._register_dashboard_and_login()
        self.app.register_blueprint(self.blueprint)

    def _register_dashboard_and_login(self):
        """Registers the main admin dashboard and handles login."""

        async def index(request):
            error = None
            if request.user and getattr(request.user, "is_admin", False):
                return self.render(request, "dashboard.html")

            if request.method == "POST":
                from models import User

                form_data = await request.form()
                username = form_data.get("username")
                password = form_data.get("password")

                user = User.query.filter_by(username=username).first()

                if user and user.is_admin and user.check_password(password):
                    response = redirect(url_for(request, "admin.index"))
                    login_user(response, user)
                    return response
                else:
                    error = "Invalid credentials or not an admin."

            return self.render(request, "login.html", context={"error": error})

        self.blueprint.add_route("/", index, endpoint="index", methods=["GET", "POST"])

    def _create_form_for_model(self, model, instance=None):
        form_fields = {}
        for column in inspect(model).c:
            if not column.primary_key:
                default_value = getattr(instance, column.name) if instance else ""
                form_fields[column.name] = StringField(
                    label=column.name.replace("_", " ").title(),
                    default=str(default_value) if default_value is not None else "",
                )
        return type(f"{model.__name__}Form", (Form,), form_fields)

    def register(self, model):
        model_name = model.__name__
        self.models[model_name] = model
        pk_name = inspect(model).primary_key[0].name

        @admin_required
        async def list_view(request):
            records = db_session.query(model).all()
            columns = [c.name for c in model.__table__.columns]
            records_data = [
                {c.name: getattr(r, c.name) for c in model.__table__.columns}
                for r in records
            ]

            AddForm = self._create_form_for_model(model)
            add_form = AddForm()

            context = {
                "model_name": model_name,
                "columns": columns,
                "records": records_data,
                "pk_name": pk_name,
                "add_form": add_form,
            }
            return self.render(request, "list.html", context=context)

        @admin_required
        async def add_view(request):
            ModelForm = self._create_form_for_model(model)
            form_data = await request.form()
            form = ModelForm(formdata=form_data)

            if form.validate():
                new_record = model()
                for field_name, field in form._fields.items():
                    setattr(new_record, field_name, field.data)
                new_record.save()
                return redirect(url_for(request, f"admin.{model_name.lower()}_list"))

            records = db_session.query(model).all()
            columns = [c.name for c in model.__table__.columns]
            records_data = [
                {c.name: getattr(r, c.name) for c in model.__table__.columns}
                for r in records
            ]
            context = {
                "model_name": model_name,
                "columns": columns,
                "records": records_data,
                "pk_name": pk_name,
                "add_form": form,
            }
            return self.render(request, "list.html", context=context)

        @admin_required
        async def edit_view(request, **kwargs):
            record_id = kwargs.get(pk_name)
            record = db_session.query(model).get(record_id)

            ModelForm = self._create_form_for_model(model, instance=record)

            if request.method == "POST":
                form_data = await request.form()
                form = ModelForm(formdata=form_data)
                if form.validate():
                    for field_name, field in form._fields.items():
                        setattr(record, field_name, field.data)
                    record.save()
                    return redirect(
                        url_for(request, f"admin.{model_name.lower()}_list")
                    )
            else:
                form = ModelForm()

            context = {
                "model_name": model_name,
                "form": form,
                "record": record,
                "pk_name": pk_name,
            }
            return self.render(request, "form.html", context=context)

        @admin_required
        async def delete_view(request, **kwargs):
            if request.method == "POST":
                record_id = kwargs.get(pk_name)
                record = db_session.query(model).get(record_id)
                if record:
                    record.delete()
            return redirect(url_for(request, f"admin.{model_name.lower()}_list"))

        self.blueprint.add_route(
            f"/{model_name.lower()}", list_view, endpoint=f"{model_name.lower()}_list"
        )
        self.blueprint.add_route(
            f"/{model_name.lower()}/add",
            add_view,
            endpoint=f"{model_name.lower()}_add",
            methods=["POST"],
        )
        self.blueprint.add_route(
            f"/{model_name.lower()}/edit/<int:{pk_name}>",
            edit_view,
            endpoint=f"{model_name.lower()}_edit",
            methods=["GET", "POST"],
        )
        self.blueprint.add_route(
            f"/{model_name.lower()}/delete/<int:{pk_name}>",
            delete_view,
            endpoint=f"{model_name.lower()}_delete",
            methods=["POST"],
        )

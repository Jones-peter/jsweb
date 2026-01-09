import argparse
import getpass
import importlib.util
import logging
import os
import secrets
import shutil
import socket
import sys

from alembic import command
from alembic.autogenerate import produce_migrations
from alembic.config import Config
from alembic.operations.ops import (
    AddColumnOp,
    AlterColumnOp,
    CreateTableOp,
    DropColumnOp,
    DropTableOp,
)
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine

from jsweb import __VERSION__
from jsweb.app import JsWebApp
from jsweb.logging_config import setup_logging
from jsweb.server import run
from jsweb.utils import get_local_ip

setup_logging()
logger = logging.getLogger(__name__)

JSWEB_DIR = os.path.dirname(__file__)
PROJECT_TEMPLATES_DIR = os.path.join(JSWEB_DIR, "project_templates")
HTML_TEMPLATES_DIR = os.path.join(JSWEB_DIR, "templates")
STATIC_DIR = os.path.join(JSWEB_DIR, "static")


class ConfigObject:
    """A simple object to hold configuration settings."""

    pass


def load_config():
    """
    Loads configuration from a 'config.py' file in the current working directory.

    This function reads the configuration file, populates a ConfigObject with its settings,
    and then overrides these settings with any environment variables prefixed with 'JSWEB_'.
    It will exit the application if the 'config.py' file cannot be found or loaded.
    """
    config_path = os.path.join(os.getcwd(), "config.py")
    if not os.path.exists(config_path):
        logger.error("❌ Error: config.py not found in the current directory.")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("user_config", config_path)
    if spec is None or spec.loader is None:
        logger.error(f"❌ Error: Could not load config.py from {config_path}")
        sys.exit(1)

    user_config_module = importlib.util.module_from_spec(spec)
    sys.modules["user_config"] = user_config_module
    spec.loader.exec_module(user_config_module)

    config = ConfigObject()
    for key in dir(user_config_module):
        if key.isupper():
            setattr(config, key, getattr(user_config_module, key))

    for key, value in os.environ.items():
        if key.startswith("JSWEB_"):
            config_key = key[len("JSWEB_") :]
            if hasattr(config, config_key):
                original_value = getattr(config, config_key)
                try:
                    if isinstance(original_value, int):
                        setattr(config, config_key, int(value))
                    elif isinstance(original_value, bool):
                        setattr(
                            config,
                            config_key,
                            value.lower() in ("true", "1", "t", "y", "yes"),
                        )
                    else:
                        setattr(config, config_key, value)
                    logger.info(
                        f"⚙️  Config override: {config_key} = {getattr(config, config_key)} (from environment variable)"
                    )
                except ValueError:
                    logger.warning(
                        f"⚠️  Could not convert environment variable JSWEB_{config_key}='{value}' to type of original value ({type(original_value).__name__}). Keeping original value."
                    )

    return config


def create_project(name):
    """
    Creates a new JsWeb project with a default directory structure and starter files.

    This function generates a new project directory and populates it with essential
    subdirectories ('templates', 'static') and files. It copies standard HTML templates
    and static assets, and renders Python source files from Jinja templates, including a
    'config.py' with a securely generated secret key.

    Args:
        name (str): The name of the project to create.
    """
    project_dir = os.path.abspath(name)
    templates_dest_dir = os.path.join(project_dir, "templates")
    static_dest_dir = os.path.join(project_dir, "static")

    os.makedirs(templates_dest_dir, exist_ok=True)
    os.makedirs(static_dest_dir, exist_ok=True)

    text_files_to_copy = {
        os.path.join(HTML_TEMPLATES_DIR, "starter_template.html"): os.path.join(
            templates_dest_dir, "welcome.html"
        ),
        os.path.join(HTML_TEMPLATES_DIR, "login.html"): os.path.join(
            templates_dest_dir, "login.html"
        ),
        os.path.join(HTML_TEMPLATES_DIR, "register.html"): os.path.join(
            templates_dest_dir, "register.html"
        ),
        os.path.join(HTML_TEMPLATES_DIR, "profile.html"): os.path.join(
            templates_dest_dir, "profile.html"
        ),
        os.path.join(STATIC_DIR, "global.css"): os.path.join(
            static_dest_dir, "global.css"
        ),
    }
    for src, dest in text_files_to_copy.items():
        with open(src, encoding="utf-8") as f_src:
            content = f_src.read()
        with open(dest, "w", encoding="utf-8") as f_dest:
            f_dest.write(content)

    binary_files_to_copy = {
        os.path.join(STATIC_DIR, "jsweb_logo.png"): os.path.join(
            static_dest_dir, "jsweb_logo.png"
        ),
        os.path.join(STATIC_DIR, "jsweb_logo_bg.png"): os.path.join(
            static_dest_dir, "jsweb_logo_bg.png"
        ),
    }
    for src, dest in binary_files_to_copy.items():
        with open(src, "rb") as f_src:
            content = f_src.read()
        with open(dest, "wb") as f_dest:
            f_dest.write(content)

    env = Environment(loader=FileSystemLoader(PROJECT_TEMPLATES_DIR), autoescape=False)

    templates_to_render = {
        "app.py.jinja": os.path.join(project_dir, "app.py"),
        "views.py.jinja": os.path.join(project_dir, "views.py"),
        "auth.py.jinja": os.path.join(project_dir, "auth.py"),
        "forms.py.jinja": os.path.join(project_dir, "forms.py"),
        "models.py.jinja": os.path.join(project_dir, "models.py"),
    }
    for template_name, dest_path in templates_to_render.items():
        template = env.get_template(template_name)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(template.render())

    config_template = env.get_template("config.py.jinja")
    with open(os.path.join(project_dir, "config.py"), "w", encoding="utf-8") as f:
        f.write(
            config_template.render(project_name=name, secret_key=secrets.token_hex(16))
        )

    logger.info(f"✔️ Project '{name}' created successfully in '{project_dir}'.")
    logger.info(
        f"👉 To get started, run:\n  cd {name}\n  jsweb db prepare\n  jsweb db upgrade\n  jsweb run"
    )


def check_port(host, port):
    """
    Checks if a given network port is available to bind to.

    Args:
        host (str): The host address to check.
        port (int): The port number to check.

    Returns:
        bool: True if the port is available, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
        return True
    except OSError:
        return False


def display_qr_code(url):
    """
    Displays a QR code in the terminal for the given URL.

    This function uses the 'qrcode' library to generate and print a QR code
    that allows easy access to the server from a mobile device on the same network.

    Args:
        url (str): The URL to encode in the QR code.
    """
    import qrcode

    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)
    logger.info("📱 Scan the QR code to access the server on your local network:")
    qr.print_tty()
    logger.info("-" * 40)


def setup_alembic_if_needed():
    """
    Initializes the Alembic migration environment if it's not already set up.

    This function checks for the existence of the 'migrations/env.py' file. If not found,
    it creates the necessary directory structure and copies pre-configured Alembic
    template files into the project, ensuring a consistent migration setup.
    """
    migrations_dir = os.path.join(os.getcwd(), "migrations")
    if not os.path.exists(os.path.join(migrations_dir, "env.py")):
        logger.info("⚙️  Initializing migration environment...")

        os.makedirs(os.path.join(migrations_dir, "versions"), exist_ok=True)

        alembic_template_dir = os.path.join(PROJECT_TEMPLATES_DIR, "alembic")
        shutil.copy(os.path.join(alembic_template_dir, "env.py"), migrations_dir)
        shutil.copy(os.path.join(alembic_template_dir, "config.ini"), migrations_dir)
        shutil.copy(
            os.path.join(alembic_template_dir, "script.py.mako"), migrations_dir
        )
        logger.info("✅ Migration environment initialized.")


def get_alembic_config(db_url):
    """
    Loads and configures the Alembic configuration for database migrations.

    Args:
        db_url (str): The database connection URL.

    Returns:
        alembic.config.Config: The configured Alembic Config object, or None if the
                               configuration file does not exist.
    """
    config_path = "migrations/config.ini"
    if not os.path.exists(config_path):
        return None

    cfg = Config(config_path)
    migrations_dir = os.path.join(os.getcwd(), "migrations")
    cfg.set_main_option("script_location", migrations_dir)
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def is_db_up_to_date(config):
    """
    Checks if the database schema is up-to-date with the latest migration script.

    Args:
        config (alembic.config.Config): The Alembic configuration object.

    Returns:
        bool: True if the database is at the latest revision, False otherwise.
    """
    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            script = ScriptDirectory.from_config(config)
            head_rev = script.get_current_head()
            return current_rev == head_rev
    except Exception:
        return False


def has_model_changes(database_url, metadata):
    """
    Detects if there are differences between SQLAlchemy models and the database schema.

    Args:
        database_url (str): The database connection URL.
        metadata (sqlalchemy.schema.MetaData): The SQLAlchemy MetaData object for the models.

    Returns:
        bool: True if changes are detected, False otherwise.
    """
    from alembic.autogenerate import compare_metadata
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    engine = create_engine(database_url)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        diffs = compare_metadata(context, metadata)
    return bool(diffs)


def preview_model_changes_readable(database_url, metadata):
    """
    Generates a human-readable summary of detected database schema changes.

    Compares the current SQLAlchemy model definitions against the database schema and
    produces a list of strings describing the required changes (e.g., create table,
    add column).

    Args:
        database_url (str): The database connection URL.
        metadata (sqlalchemy.schema.MetaData): The SQLAlchemy MetaData object for the models.

    Returns:
        list[str] or None: A list of strings describing the changes, or None if no
                           changes are detected.
    """
    engine = create_engine(database_url)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        migration_script = produce_migrations(context, metadata)
        changes = []
        for op in migration_script.upgrade_ops.ops:
            if isinstance(op, CreateTableOp):
                changes.append(f"Create table '{op.table_name}'")
            elif isinstance(op, DropTableOp):
                changes.append(f"Drop table '{op.table_name}'")
            elif isinstance(op, AddColumnOp):
                changes.append(
                    f"Add column '{op.column.name}' to table '{op.table_name}'"
                )
            elif isinstance(op, DropColumnOp):
                changes.append(
                    f"Drop column '{op.column_name}' from table '{op.table_name}'"
                )
            elif isinstance(op, AlterColumnOp):
                changes.append(
                    f"Alter column '{op.column_name}' in table '{op.table_name}'"
                )
            else:
                changes.append(f"Unhandled change: {op.__class__.__name__}")
        return changes if changes else None


def create_admin_user():
    """
    Interactively creates a new administrative user in the database.

    This function prompts the user for a username, email, and password. It then
    validates the input, checks for existing users, and creates a new user with
    administrative privileges.
    """
    logger.info("Creating a new admin user...")
    from jsweb.database import db_session, init_db

    config = load_config()
    init_db(config.DATABASE_URL)

    try:
        from models import User

        username = input("Username: ")
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm Password: ")

        if password != confirm_password:
            logger.error("❌ Passwords do not match.")
            return

        if User.query.filter_by(username=username).first():
            logger.error(f"❌ User with username '{username}' already exists.")
            return

        if User.query.filter_by(email=email).first():
            logger.error(f"❌ User with email '{email}' already exists.")
            return

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        admin.save()

        db_session.commit()

        logger.info(f"✅ Admin user '{username}' created successfully.")

    except ImportError:
        logger.error(
            "❌ Could not import User model. Make sure you are in a JsWeb project directory."
        )
    except Exception as e:
        db_session.rollback()
        logger.error(f"❌ An error occurred: {e}")
    finally:
        db_session.remove()


def cli():
    """
    The main entry point for the JsWeb command-line interface.

    This function parses command-line arguments and executes the corresponding
    actions, such as running the development server, creating a new project,
    or managing database migrations.
    """
    parser = argparse.ArgumentParser(
        prog="jsweb", description="JsWeb CLI - A lightweight Python web framework."
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__VERSION__}"
    )
    sub = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    run_cmd = sub.add_parser(
        "run", help="Run the JsWeb application in the current directory."
    )
    run_cmd.add_argument(
        "--host", default=None, help="Host address to bind to (overrides config)"
    )
    run_cmd.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port number to listen on (overrides config)",
    )
    run_cmd.add_argument(
        "--qr",
        action="store_true",
        help="Display a QR code for the server's LAN access.",
    )
    run_cmd.add_argument(
        "--reload", action="store_true", help="Enable auto-reloading for development."
    )

    new_cmd = sub.add_parser("new", help="Create a new JsWeb project.")
    new_cmd.add_argument("name", help="The name of the new project")

    db_cmd = sub.add_parser("db", help="Database migration tools")
    db_sub = db_cmd.add_subparsers(
        dest="subcommand", help="Migration actions", required=True
    )

    prepare_cmd = db_sub.add_parser(
        "prepare", help="Detect model changes and create a migration script."
    )
    prepare_cmd.add_argument(
        "-m",
        "--message",
        required=False,
        help="A short, descriptive message for the migration.",
    )

    db_sub.add_parser("upgrade", help="Apply all pending migrations to the database.")

    sub.add_parser("create-admin", help="Create a new administrator user.")

    args = parser.parse_args()
    sys.path.insert(0, os.getcwd())

    if args.command == "run":
        config = load_config()

        app_path = os.path.join(os.getcwd(), "app.py")
        if not os.path.exists(app_path):
            logger.error(
                "❌ Error: Could not find 'app.py'. Ensure you are in a JsWeb project directory."
            )
            return

        try:
            spec = importlib.util.spec_from_file_location("user_app", app_path)
            user_app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(user_app_module)

            app_instance = None
            for obj in vars(user_app_module).values():
                if isinstance(obj, JsWebApp):
                    app_instance = obj
                    break

            if not app_instance:
                raise AttributeError(
                    "Could not find an instance of JsWebApp in your app.py file."
                )

            app_instance.config = config
            app_instance._init_from_config()

            from jsweb.database import init_db

            init_db(config.DATABASE_URL)

            if getattr(config, "ENABLE_OPENAPI_DOCS", True):
                try:
                    from jsweb.docs import setup_openapi_docs
                    from jsweb.docs.introspection import introspect_app_routes

                    introspect_app_routes(app_instance)

                    setup_openapi_docs(
                        app_instance,
                        title=getattr(config, "API_TITLE", "jsweb API"),
                        version=getattr(config, "API_VERSION", "1.0.0"),
                        description=getattr(config, "API_DESCRIPTION", ""),
                        docs_url=getattr(config, "OPENAPI_DOCS_URL", "/docs"),
                        redoc_url=getattr(config, "OPENAPI_REDOC_URL", "/redoc"),
                        openapi_url=getattr(
                            config, "OPENAPI_JSON_URL", "/openapi.json"
                        ),
                    )
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"⚠️  Could not setup OpenAPI docs: {e}")

            host = args.host or config.HOST
            port = args.port or config.PORT

            if not check_port(host, port):
                logger.error(
                    f"❌ Error: Port {port} is already in use. Please specify a different port using --port."
                )
                return

            if args.qr:
                lan_ip = get_local_ip()
                url = f"http://{lan_ip}:{port}"
                display_qr_code(url)

            run(app_instance, host=host, port=port, reload=args.reload)

        except Exception as e:
            logger.error(f"❌ Error: Failed to run app. Details: {e}")

    elif args.command == "new":
        create_project(args.name)

    elif args.command == "create-admin":
        create_admin_user()

    elif args.command == "db":
        config = load_config()
        try:
            import models

            from jsweb.database import init_db

            init_db(config.DATABASE_URL)
        except Exception as e:
            logger.error(f"❌ Error importing models or initializing DB: {e}")
            return

        setup_alembic_if_needed()
        alembic_cfg = get_alembic_config(config.DATABASE_URL)

        if args.subcommand == "prepare":
            if not is_db_up_to_date(alembic_cfg):
                logger.error(
                    "❌ Cannot prepare new migration: Your database is not up to date."
                )
                logger.info(
                    "👉 Run `jsweb db upgrade` first to apply existing migrations."
                )
                return
            if not has_model_changes(config.DATABASE_URL, models.ModelBase.metadata):
                logger.info("✅ No changes detected in models.")
                return

            changes = preview_model_changes_readable(
                config.DATABASE_URL, models.ModelBase.metadata
            )
            if not changes:
                logger.info("✅ No changes detected in models.")
                return

            logger.info("📋 The following changes will be applied:")
            logger.info("=" * 40)
            for change in changes:
                logger.info(change)
            logger.info("=" * 40)

            message = args.message
            if not message:
                message = ", ".join(changes)
                logger.info(f"💬 Auto-generated message: {message}")

            command.revision(alembic_cfg, autogenerate=True, message=message)
            logger.info("✅ Migration script prepared.")

        elif args.subcommand == "upgrade":
            command.upgrade(alembic_cfg, "head")
            logger.info("✅ Database upgrade complete.")

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()

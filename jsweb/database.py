from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker

Session = sessionmaker(expire_on_commit=False)
db_session = scoped_session(Session)

Base = declarative_base()
Base.query = db_session.query_property()

_engine = None


def init_db(database_url, echo=False):
    """
    Initializes the database engine and configures the session factory.

    This function sets up the connection to the database using the provided URL and
    binds the engine to the session factory and the declarative base. It should be
    called once when the application starts.

    Args:
        database_url (str): The connection string for the database.
        echo (bool): If True, the engine will log all statements. Defaults to False.
    """
    global _engine
    _engine = create_engine(database_url, echo=echo)
    Session.configure(bind=_engine)
    Base.metadata.bind = _engine


def get_engine():
    """
    Returns the database engine instance.

    Raises:
        RuntimeError: If the database engine has not been initialized by calling `init_db()`.

    Returns:
        sqlalchemy.engine.Engine: The active SQLAlchemy engine instance.
    """
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Call init_db() first.")
    return _engine


class DatabaseError(Exception):
    """Custom exception raised for database operation failures."""

    pass


def _handle_db_error(e):
    """
    Rolls back the session and raises a custom DatabaseError.

    This is an internal helper to provide consistent error handling for database
    operations within the ModelBase class. It rolls back the current transaction
    and wraps the original SQLAlchemy exception in a custom DatabaseError.

    Args:
        e (SQLAlchemyError): The original exception from SQLAlchemy.

    Raises:
        DatabaseError: A custom exception wrapping the original error.
    """
    db_session.rollback()
    if isinstance(e, IntegrityError):
        simple_message = str(e.orig)
        raise DatabaseError(f"Constraint failed: {simple_message}") from e
    else:
        raise DatabaseError(f"Database operation failed: {e}") from e


class ModelBase(Base):
    """
    An abstract base model that provides convenience methods for database operations.

    Inherit from this class to give your models helper methods like `save()`, `delete()`,
    `update()`, and `create()`. It also ensures that all models share the same
    declarative base.
    """

    __abstract__ = True

    @classmethod
    def create(cls, **kwargs):
        """
        Create and save a new model instance in a single step.

        Args:
            **kwargs: The attributes for the new model instance.

        Returns:
            The newly created model instance.
        """
        instance = cls(**kwargs)
        instance.save()
        return instance

    def update(self, **kwargs):
        """
        Update attributes of the model instance and save the changes.

        Args:
            **kwargs: The attributes to update on the model instance.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

    def save(self):
        """
        Adds the object to the session.

        The actual database commit is typically managed by a middleware at the end
        of the request-response cycle. This method handles adding the instance to
        the session and provides error handling.
        """
        try:
            db_session.add(self)
        except SQLAlchemyError as e:
            _handle_db_error(e)

    def delete(self):
        """
        Deletes the object from the session.

        The actual database commit is typically managed by a middleware at the end
        of the request-response cycle. This method handles marking the instance for
        deletion and provides error handling.
        """
        try:
            db_session.delete(self)
        except SQLAlchemyError as e:
            _handle_db_error(e)

    def to_dict(self):
        """
        Returns a dictionary representation of the model's columns.

        This method inspects the model's mapped columns and returns a dictionary
        containing the key-value pairs for the instance's data.

        Returns:
            dict: A dictionary representation of the model instance.
        """
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


__all__ = [
    "init_db",
    "get_engine",
    "db_session",
    "ModelBase",
    "Base",
    "DatabaseError",
    "Integer",
    "String",
    "Float",
    "Boolean",
    "DateTime",
    "Text",
    "Column",
    "ForeignKey",
    "relationship",
    "UniqueConstraint",
]

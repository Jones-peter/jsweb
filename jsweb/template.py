"""
This module provides a simple interface for rendering Jinja2 templates.

It manages a global Jinja2 environment and provides functions for rendering
templates and adding custom filters.
"""

import os

from jinja2 import Environment, FileSystemLoader

_env = None


def get_env():
    """
    Initializes and returns the global Jinja2 environment.

    The environment is configured to load templates from a 'templates' directory
    located in the current working directory. The environment is created only on
    the first call and then cached.

    Returns:
        jinja2.Environment: The global Jinja2 environment.
    """
    global _env
    if _env is None:
        _env = Environment(
            loader=FileSystemLoader(os.path.join(os.getcwd(), "templates"))
        )
    return _env


def add_filter(name, func):
    """
    Adds a custom filter to the Jinja2 environment.

    Args:
        name (str): The name of the filter.
        func (callable): The filter function.
    """
    env = get_env()
    env.filters[name] = func


def render(template_name, context=None):
    """
    Renders a template with the given context.

    Args:
        template_name (str): The name of the template file to render.
        context (dict, optional): A dictionary of context variables to pass
                                  to the template. Defaults to None.

    Returns:
        str: The rendered template as a string.
    """
    if context is None:
        context = {}
    env = get_env()
    template = env.get_template(template_name)
    return template.render(**context)

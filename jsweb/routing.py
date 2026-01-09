from __future__ import annotations

import re
import uuid
from collections.abc import Callable


class NotFound(Exception):
    """Raised when a route is not found for a given path."""

    pass


class MethodNotAllowed(Exception):
    """Raised when a request method is not allowed for a matched route."""

    pass


def _int_converter(value: str) -> int | None:
    """
    Converts a string to an integer. Handles negative numbers with validation.

    Args:
        value (str): The string to convert.

    Returns:
        Optional[int]: The converted integer, or None if conversion fails or out of range.
    """
    # Prevent excessive length inputs (DoS protection)
    if len(value) > 15:
        return None

    try:
        if value.startswith("-") and value[1:].isdigit():
            result = int(value)
        elif value.isdigit():
            result = int(value)
        else:
            return None

        # Validate range to prevent overflow (32-bit signed integer range)
        if abs(result) > 2147483647:  # 2^31 - 1
            return None

        return result
    except (ValueError, OverflowError):
        return None


def _float_converter(value: str) -> float | None:
    """
    Converts a string to a float.

    Args:
        value (str): The string to convert.

    Returns:
        Optional[float]: The converted float, or None if conversion fails.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _uuid_converter(value: str) -> uuid.UUID | None:
    """
    Converts a string to a UUID.

    Args:
        value (str): The string to convert.

    Returns:
        Optional[uuid.UUID]: The converted UUID, or None if conversion fails.
    """
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _str_converter(value: str) -> str | None:
    """
    A converter for string parameters with length validation.

    Args:
        value (str): The string to validate.

    Returns:
        Optional[str]: The string if valid, None if too long.
    """
    # Limit string parameter length to prevent DoS
    if len(value) > 1000:
        return None
    return value


def _path_converter(value: str) -> str | None:
    """
    A converter for path parameters with length validation.
    Can include slashes.

    Args:
        value (str): The path string to validate.

    Returns:
        Optional[str]: The path if valid, None if too long.
    """
    # Limit path parameter length to prevent DoS
    if len(value) > 2000:
        return None
    return value


class Route:
    """
    Represents a single route, mapping a URL path to a handler function.

    It compiles the path into a regular expression for efficient matching of
    dynamic segments and handles parameter type conversion.

    Attributes:
        path (str): The URL path pattern (e.g., '/users/<int:user_id>').
        handler (Callable): The view function to execute for this route.
        methods (List[str]): A list of allowed HTTP methods (e.g., ['GET', 'POST']).
        endpoint (str): A unique name for the route, used for URL generation.
        is_static (bool): A flag indicating if the route has dynamic parameters.
    """

    __slots__ = (
        "path",
        "handler",
        "methods",
        "endpoint",
        "converters",
        "is_static",
        "regex",
        "param_names",
    )

    TYPE_CONVERTERS = {
        "str": (_str_converter, r"[^/]+"),
        "int": (_int_converter, r"-?\d+"),
        "float": (_float_converter, r"-?\d+(\.\d+)?"),
        "uuid": (
            _uuid_converter,
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        ),
        "path": (_path_converter, r".+?"),
    }

    def __init__(self, path: str, handler: Callable, methods: list[str], endpoint: str):
        self.path = path
        self.handler = handler
        self.methods = methods
        self.endpoint = endpoint
        self.converters = {}
        self.is_static = "<" not in path
        if not self.is_static:
            self.regex, self.param_names = self._compile_path()
        else:
            self.regex = None
            self.param_names = []

    def _compile_path(self):
        """
        Compiles the path string into a regular expression for matching.

        It extracts parameter names and their types, storing the appropriate
        converters and building a regex that captures the dynamic parts of the URL.

        Returns:
            (re.Pattern, List[str]): A tuple containing the compiled regex and a
                                     list of parameter names.
        """
        param_defs = re.findall(r"<(\w+):(\w+)>", self.path)
        regex_path = "^" + self.path + "$"
        param_names = []

        for type_name, param_name in param_defs:
            converter, regex_part = self.TYPE_CONVERTERS.get(
                type_name, self.TYPE_CONVERTERS["str"]
            )
            regex_path = regex_path.replace(
                f"<{type_name}:{param_name}>", f"(?P<{param_name}>{regex_part})"
            )
            self.converters[param_name] = converter
            param_names.append(param_name)

        return re.compile(regex_path), param_names

    def match(self, path: str) -> dict[str, any] | None:
        """
        Matches the given path against the route and extracts parameters.

        For static routes, it performs a simple string comparison. For dynamic routes,
        it uses the pre-compiled regex and applies type converters to the captured values.

        Args:
            path (str): The request path to match.

        Returns:
            Optional[Dict[str, any]]: A dictionary of matched parameters if the path
                                      matches, otherwise None.
        """
        if self.is_static:
            return {} if path == self.path else None

        match = self.regex.match(path)
        if not match:
            return None

        params = match.groupdict()
        try:
            for name, value in params.items():
                params[name] = self.converters[name](value)
            return params
        except (ValueError, TypeError):
            return None


class Router:
    """
    Manages a collection of routes and resolves incoming requests to the correct handler.

    It provides methods for adding routes, a decorator for registering view functions,
    and functionality for reverse URL generation (`url_for`).
    """

    def __init__(self):
        self.static_routes: dict[str, Route] = {}
        self.dynamic_routes: list[Route] = []
        self.endpoints: dict[str, Route] = {}

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: list[str] | None = None,
        endpoint: str | None = None,
    ):
        """
        Adds a new route to the router.

        Args:
            path (str): The URL path pattern.
            handler (Callable): The view function.
            methods (Optional[List[str]]): A list of allowed HTTP methods. Defaults to ['GET'].
            endpoint (Optional[str]): A unique name for the route. Defaults to the handler's name.

        Raises:
            ValueError: If the endpoint name is already registered.
        """
        if methods is None:
            methods = ["GET"]

        if endpoint is None:
            endpoint = handler.__name__

        if endpoint in self.endpoints:
            raise ValueError(f'Endpoint "{endpoint}" is already registered.')

        route = Route(path, handler, methods, endpoint)

        if route.is_static:
            self.static_routes[path] = route
        else:
            self.dynamic_routes.append(route)

        self.endpoints[endpoint] = route

    def route(
        self,
        path: str,
        methods: list[str] | None = None,
        endpoint: str | None = None,
    ):
        """
        A decorator to register a view function for a given URL path.

        Example:
            @router.route('/users/<int:user_id>')
            def get_user(req, user_id):
                ...

        Args:
            path (str): The URL path pattern.
            methods (Optional[List[str]]): A list of allowed HTTP methods.
            endpoint (Optional[str]): A unique name for the route.

        Returns:
            Callable: The decorator.
        """

        def decorator(handler):
            self.add_route(path, handler, methods, endpoint)
            return handler

        return decorator

    def resolve(self, path: str, method: str) -> (Callable, dict[str, any]):
        """
        Finds the handler and parameters for a given path and HTTP method.

        It prioritizes static routes for performance.

        Args:
            path (str): The request path.
            method (str): The HTTP request method.

        Returns:
            (Callable, Dict[str, any]): A tuple containing the matched handler and a
                                         dictionary of URL parameters.

        Raises:
            NotFound: If no route matches the path.
            MethodNotAllowed: If a route matches but not for the given method.
        """
        if path in self.static_routes:
            route = self.static_routes[path]
            if method in route.methods:
                return route.handler, {}
            raise MethodNotAllowed(f"Method {method} not allowed for path {path}.")

        for route in self.dynamic_routes:
            if method not in route.methods:
                continue
            params = route.match(path)
            if params is not None:
                return route.handler, params
        raise NotFound(f"No route found for {path}")

    def url_for(self, endpoint: str, **params) -> str:
        """
        Generates a URL for a given endpoint and parameters.

        Args:
            endpoint (str): The name of the endpoint to generate a URL for.
            **params: The values for the dynamic parameters in the URL.

        Returns:
            str: The generated URL path.

        Raises:
            ValueError: If the endpoint is not found or a required parameter is missing.
        """
        if endpoint not in self.endpoints:
            raise ValueError(f"No route found for endpoint '{endpoint}'.")

        route = self.endpoints[endpoint]
        path = route.path

        if route.is_static:
            return path

        for param_name in route.param_names:
            if param_name not in params:
                raise ValueError(
                    f"Missing parameter '{param_name}' for endpoint '{endpoint}'."
                )

            for type_name in Route.TYPE_CONVERTERS.keys():
                pattern = f"<{type_name}:{param_name}>"
                if pattern in path:
                    path = path.replace(pattern, str(params[param_name]))
                    break

        return path

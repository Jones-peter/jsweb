import re
from typing import Dict, List, Optional, Callable


class NotFound(Exception):
    """
    Raised when a route is not found.
    """
    pass


class MethodNotAllowed(Exception):
    """
    Raised when a method is not allowed for a route.
    """
    pass


# We define typed converters instead of using regex
def _int_converter(value: str) -> Optional[int]:
    """
    Optimized integer converter using str.isdigit().
    """
    # we also handle negative integers
    if value.startswith('-') and value[1:].isdigit():
        return int(value)
    return int(value) if value.isdigit() else None


def _str_converter(value: str) -> str:
    """String passthrough - no conversion needed."""
    return value


def _path_converter(value: str) -> str:
    """Path passthrough - accepts any string including slashes."""
    return value


class Route:
    """
    Represents a single route with path, handler, and parameter conversion.
    """

    # We use __slots__ to reduce memory usage and to speed up attribute access
    __slots__ = ('path', 'handler', 'methods', 'endpoint', 'converters',
                 'is_static', 'regex', 'param_names')

    # Class-level type converters - optimized functions instead of just type constructors
    TYPE_CONVERTERS = {
        'str': (_str_converter, r'[^/]+'),
        'int': (_int_converter, r'-?\d+'),  # Allow optional negative sign
        'path': (_path_converter, r'.+?')
    }

    def __init__(self, path: str, handler: Callable, methods: List[str], endpoint: str):
        self.path = path
        self.handler = handler
        self.methods = methods  # List is faster than set for small N (1-3 methods)
        self.endpoint = endpoint
        self.converters = {}
        self.is_static = '<' not in path  # Flag for static routes
        if not self.is_static:
            self.regex, self.param_names = self._compile_path()
        else:
            self.regex = None
            self.param_names = []
        

    def _compile_path(self):
        """
        Compiles the path into a regex and extracts parameter converters.
        """
        
        param_defs = re.findall(r"<(\w+):(\w+)>", self.path)
        regex_path = "^" + self.path + "$"
        param_names = []

        for type_name, param_name in param_defs:
            converter, regex_part = self.TYPE_CONVERTERS.get(type_name, self.TYPE_CONVERTERS['str'])
            regex_path = regex_path.replace(f"<{type_name}:{param_name}>", f"(?P<{param_name}>{regex_part})")
            self.converters[param_name] = converter
            param_names.append(param_name)

        return re.compile(regex_path), param_names

    def match(self, path):
        """
        Matches the given path against the route's regex and returns converted parameters.
        """

        #For static routes, string comparison is much faster than regex
        if self.is_static:
            return {} if path == self.path else None
        
        # For dynamic routes, use pre-compiled regex
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
    Handles routing by mapping URL paths to view functions and endpoint names.
    """
    def __init__(self):
        self.static_routes: Dict[str, Route] = {}
        self.dynamic_routes: List[Route] = []
        self.endpoints: Dict[str, Route] = {}  # For reverse lookups (url_for)


    def add_route(self, path: str, handler: Callable, methods: Optional[List[str]]=None, endpoint: Optional[str]=None):
        """
        Adds a new route to the router.
        """
        if methods is None:
            methods = ["GET"]
        
        if endpoint is None:
            endpoint = handler.__name__

        if endpoint in self.endpoints:
            raise ValueError(f"Endpoint \"{endpoint}\" is already registered.")

        route = Route(path, handler, methods, endpoint)

        if route.is_static:
            self.static_routes[path] = route
        else:
            self.dynamic_routes.append(route)
        
        self.endpoints[endpoint] = route

    def route(self, path: str, methods:Optional[List[str]]=None, endpoint:Optional[str]=None):
        """
        A decorator to register a view function for a given URL path.
        """
        def decorator(handler):
            self.add_route(path, handler, methods, endpoint)
            return handler
        return decorator

    def resolve(self, path, method):
        """
        Finds the appropriate handler for a given path and HTTP method.
        """
        # Static routes: O(1) dict lookup + O(k) method check (k=1-3)
        if path in self.static_routes:
            route = self.static_routes[path]
            if method in route.methods:
                return route.handler, {}
            raise MethodNotAllowed(f"Method {method} not allowed for path {path}.")

        # Dynamic routes: Check method before expensive regex matching
        for route in self.dynamic_routes:
            if method not in route.methods:  # Quick rejection for mismatched methods
                continue
            # Now do the expensive regex matching
            params = route.match(path)
            if params is not None:
                return route.handler, params
        raise NotFound(f"No route found for {path}")

    def url_for(self, endpoint, **params):
        """
        Generates a URL for a given endpoint and parameters.
        """
        if endpoint not in self.endpoints:
            raise ValueError(f"No route found for endpoint '{endpoint}'.")

        route = self.endpoints[endpoint]
        path = route.path

        if route.is_static:
            return path

        for param_name in route.param_names:
            if param_name not in params:
                raise ValueError(f"Missing parameter '{param_name}' for endpoint '{endpoint}'.")
            
            for type_name in Route.TYPE_CONVERTERS.keys():
                pattern = f"<{type_name}:{param_name}>"
                if pattern in path:
                    path = path.replace(pattern, str(params[param_name]))
                    break
        
        return path

from __future__ import annotations

from collections.abc import Callable


class Blueprint:
    """
    Represents a blueprint, a collection of routes that can be registered with an application.

    Blueprints are used to structure a JsWeb application into smaller, reusable
    components. Each blueprint can have its own routes, URL prefix, and static
    files. This helps in organizing code and promoting modularity.
    """

    def __init__(
        self,
        name: str,
        url_prefix: str | None = None,
        static_folder: str | None = None,
        static_url_path: str | None = None,
    ):
        """
        Initializes a new Blueprint.

        Args:
            name: The name of the blueprint, used for endpoint namespacing.
            url_prefix: An optional prefix for all routes defined in this blueprint.
                        For example, if a prefix is '/api' and a route is '/users',
                        the final path will be '/api/users'.
            static_folder: The name of the folder containing static files for this
                           blueprint, relative to the blueprint's location.
            static_url_path: The URL path where the blueprint's static files will be
                             served from. Defaults to the static folder name if not provided.
        """
        self.name = name
        self.url_prefix = url_prefix
        self.routes: list[tuple[str, Callable, list[str], str]] = []
        self.static_folder = static_folder
        self.static_url_path = static_url_path

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: list[str] | None = None,
        endpoint: str | None = None,
    ):
        """
        Programmatically adds a route to the blueprint.

        This method is an alternative to the `@route` decorator and is useful for
        dynamically generated views, such as those in a class-based view system
        or an admin panel.

        Args:
            path: The URL path for the route.
            handler: The view function that will handle requests to this path.
            methods: A list of allowed HTTP methods (e.g., ["GET", "POST"]).
                     Defaults to ["GET"].
            endpoint: A unique name for this route's endpoint. If not provided,
                      it defaults to the name of the handler function.
        """
        if methods is None:
            methods = ["GET"]

        route_endpoint = endpoint or handler.__name__
        self.routes.append((path, handler, methods, route_endpoint))

    def route(
        self,
        path: str,
        methods: list[str] | None = None,
        endpoint: str | None = None,
    ) -> Callable:
        """
        A decorator to register a view function for a given path within the blueprint.

        Example:
            bp = Blueprint('my_app')

            @bp.route('/index', methods=['GET'])
            def index(request):
                return "Hello, World!"

        Args:
            path: The URL path for the route.
            methods: A list of allowed HTTP methods. Defaults to ["GET"].
            endpoint: A unique name for the endpoint. Defaults to the function name.

        Returns:
            A decorator function that registers the view.
        """

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, methods, endpoint)
            return handler

        return decorator

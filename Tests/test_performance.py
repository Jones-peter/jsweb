"""Framework comparison and performance benchmarking tests."""

import time

import pytest


@pytest.mark.slow
@pytest.mark.integration
def test_jsweb_routing_performance():
    """Benchmark JsWeb routing performance."""
    from jsweb.routing import Router

    router = Router()

    # Add 50 static routes
    for i in range(50):
        router.add_route(
            f"/static/page/{i}",
            lambda req: "OK",
            methods=["GET"],
            endpoint=f"static_{i}",
        )

    # Add 50 dynamic routes
    for i in range(50):
        router.add_route(
            f"/dynamic/<int:id>/resource/{i}", lambda req: "OK", endpoint=f"dynamic_{i}"
        )

    # Benchmark static route resolution
    start = time.perf_counter()
    for _ in range(10000):
        router.resolve("/static/page/25", "GET")
    static_time = (time.perf_counter() - start) * 1000

    # Benchmark dynamic route resolution
    start = time.perf_counter()
    for _ in range(10000):
        router.resolve("/dynamic/123/resource/25", "GET")
    dynamic_time = (time.perf_counter() - start) * 1000

    # Assertions - JsWeb should be reasonably fast
    # Static route resolution should be < 500ms for 10k requests (~50μs per request)
    assert (
        static_time < 500
    ), f"Static routing too slow: {static_time}ms for 10k requests"

    # Dynamic route resolution should be < 1000ms for 10k requests (~100μs per request)
    assert (
        dynamic_time < 1000
    ), f"Dynamic routing too slow: {dynamic_time}ms for 10k requests"


@pytest.mark.unit
def test_jsweb_routing_accuracy_with_dynamic_routes():
    """Test that JsWeb routing correctly extracts dynamic parameters."""
    from jsweb.routing import Router

    router = Router()

    def handler(req):
        return "OK"

    router.add_route(
        "/users/<int:user_id>/posts/<int:post_id>", handler, endpoint="user_post"
    )

    # Test with various parameter values
    test_cases = [
        ("/users/1/posts/1", {"user_id": 1, "post_id": 1}),
        ("/users/999/posts/555", {"user_id": 999, "post_id": 555}),
        ("/users/0/posts/0", {"user_id": 0, "post_id": 0}),
    ]

    for path, expected_params in test_cases:
        resolved_handler, params = router.resolve(path, "GET")
        assert resolved_handler == handler, f"Handler mismatch for {path}"
        assert (
            params == expected_params
        ), f"Parameters mismatch for {path}: got {params}, expected {expected_params}"


@pytest.mark.integration
@pytest.mark.slow
def test_starlette_routing_performance():
    """Benchmark Starlette routing performance (if available)."""
    try:
        from starlette.routing import Route
        from starlette.routing import Router as StarletteRouter
    except ImportError:
        pytest.skip("Starlette not installed")

    def dummy_handler(request):
        return {"message": "OK"}

    routes = []
    for i in range(50):
        routes.append(Route(f"/static/page/{i}", dummy_handler))
        routes.append(Route(f"/dynamic/{{id:int}}/resource/{i}", dummy_handler))

    router = StarletteRouter(routes=routes)

    # Benchmark static route
    start = time.perf_counter()
    for _ in range(1000):
        scope = {"type": "http", "method": "GET", "path": "/static/page/25"}
        for route in router.routes:
            match, child_scope = route.matches(scope)
            if match:
                break
    static_time = (time.perf_counter() - start) * 1000

    # Benchmark dynamic route
    start = time.perf_counter()
    for _ in range(1000):
        scope = {"type": "http", "method": "GET", "path": "/dynamic/123/resource/25"}
        for route in router.routes:
            match, child_scope = route.matches(scope)
            if match:
                break
    dynamic_time = (time.perf_counter() - start) * 1000

    # Starlette should handle 1000 requests in reasonable time
    assert static_time < 100, f"Starlette static routing too slow: {static_time}ms"
    assert dynamic_time < 100, f"Starlette dynamic routing too slow: {dynamic_time}ms"


@pytest.mark.integration
@pytest.mark.slow
def test_flask_routing_performance():
    """Benchmark Flask routing performance (if available)."""
    try:
        from flask import Flask
        from werkzeug.routing import Map, Rule
    except ImportError:
        pytest.skip("Flask not installed")

    rules = []
    for i in range(50):
        rules.append(Rule(f"/static/page/{i}", endpoint=f"static_{i}"))
        rules.append(Rule(f"/dynamic/<int:id>/resource/{i}", endpoint=f"dynamic_{i}"))

    url_map = Map(rules)
    adapter = url_map.bind("example.com")

    # Benchmark static route
    start = time.perf_counter()
    for _ in range(10000):
        adapter.match("/static/page/25")
    static_time = (time.perf_counter() - start) * 1000

    # Benchmark dynamic route
    start = time.perf_counter()
    for _ in range(10000):
        adapter.match("/dynamic/123/resource/25")
    dynamic_time = (time.perf_counter() - start) * 1000

    # Flask should handle requests reasonably fast (adjusted for CI/CD environments)
    assert static_time < 200, f"Flask static routing too slow: {static_time}ms"
    assert dynamic_time < 300, f"Flask dynamic routing too slow: {dynamic_time}ms"


@pytest.mark.unit
def test_routing_comparison_jsweb_vs_alternatives():
    """Test and compare JsWeb routing against simple alternatives."""
    import re

    from jsweb.routing import Router

    # JsWeb router
    jsweb_router = Router()

    def handler(req):
        return "OK"

    jsweb_router.add_route("/users/<int:user_id>", handler, endpoint="jsweb_user")

    # Simple regex-based router for comparison
    class SimpleRouter:
        def __init__(self):
            self.patterns = []

        def add_route(self, path, handler):
            # Convert Flask-style path to regex
            regex_path = (
                "^"
                + re.sub(r"<int:(\w+)>", lambda m: f"(?P<{m.group(1)}>\\d+)", path)
                + "$"
            )
            self.patterns.append((re.compile(regex_path), handler))

        def resolve(self, path):
            for pattern, handler in self.patterns:
                match = pattern.match(path)
                if match:
                    return handler, match.groupdict()
            return None, None

    simple_router = SimpleRouter()
    simple_router.add_route("/users/<int:user_id>", handler)

    # Both should resolve the same path correctly
    jsweb_handler, jsweb_params = jsweb_router.resolve("/users/42", "GET")
    simple_handler, simple_params = simple_router.resolve("/users/42")

    assert jsweb_handler == handler
    assert jsweb_params == {"user_id": 42}
    assert simple_handler == handler
    assert simple_params == {"user_id": "42"}  # Regex captures as string


@pytest.mark.unit
def test_routing_with_multiple_parameter_types():
    """Test routing with different parameter types."""
    from jsweb.routing import Router

    router = Router()

    def handler(req):
        return "OK"

    # String parameter
    router.add_route("/profile/<str:username>", handler, endpoint="profile")
    handler_result, params = router.resolve("/profile/john_doe", "GET")
    assert params == {"username": "john_doe"}

    # Integer parameter
    router.add_route("/posts/<int:post_id>", handler, endpoint="post")
    handler_result, params = router.resolve("/posts/123", "GET")
    assert params == {"post_id": 123}

    # Path parameter (catch-all)
    router.add_route("/files/<path:filepath>", handler, endpoint="file")
    handler_result, params = router.resolve("/files/docs/readme.md", "GET")
    assert params.get("filepath") == "docs/readme.md"


@pytest.mark.slow
def test_router_with_many_routes():
    """Test router performance with a large number of routes."""
    from jsweb.routing import Router

    router = Router()

    def handler(req):
        return "OK"

    # Add 500 routes
    for i in range(500):
        router.add_route(f"/api/endpoint_{i}", handler, endpoint=f"endpoint_{i}")

    # Should still resolve quickly
    start = time.perf_counter()
    for _ in range(1000):
        router.resolve("/api/endpoint_250", "GET")
    elapsed = (time.perf_counter() - start) * 1000

    # Resolution should still be fast with many routes
    assert elapsed < 10, f"Too slow with 500 routes: {elapsed}ms for 1000 requests"

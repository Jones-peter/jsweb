"""Tests for jsweb routing system."""

import pytest
from jsweb.routing import Router


@pytest.mark.unit
def test_router_creation():
    """Test basic router creation."""
    router = Router()
    assert router is not None
    assert hasattr(router, 'add_route')
    assert hasattr(router, 'resolve')


@pytest.mark.unit
def test_add_static_route():
    """Test adding a static route."""
    router = Router()
    
    def handler(req):
        return "OK"
    
    router.add_route("/test", handler, methods=["GET"], endpoint="test_endpoint")
    
    # Verify route was added
    handler_result, params = router.resolve("/test", "GET")
    assert handler_result is not None
    assert params == {}


@pytest.mark.unit
def test_resolve_static_route():
    """Test resolving a static route."""
    router = Router()
    
    def handler(req):
        return "Static Response"
    
    router.add_route("/home", handler, methods=["GET"], endpoint="home")
    
    handler_result, params = router.resolve("/home", "GET")
    assert handler_result == handler
    assert params == {}


@pytest.mark.unit
def test_resolve_dynamic_route_with_int():
    """Test resolving a dynamic route with integer parameter."""
    router = Router()
    
    def handler(req, user_id):
        return f"User {user_id}"
    
    router.add_route("/users/<int:user_id>", handler, methods=["GET"], endpoint="user_detail")
    
    handler_result, params = router.resolve("/users/123", "GET")
    assert handler_result == handler
    assert params == {'user_id': 123}
    assert isinstance(params['user_id'], int)


@pytest.mark.unit
def test_resolve_multiple_dynamic_parameters():
    """Test resolving routes with multiple dynamic parameters."""
    router = Router()
    
    def handler(req, user_id, post_id):
        return f"User {user_id} Post {post_id}"
    
    router.add_route("/users/<int:user_id>/posts/<int:post_id>", handler, endpoint="user_post")
    
    handler_result, params = router.resolve("/users/42/posts/100", "GET")
    assert handler_result == handler
    assert params == {'user_id': 42, 'post_id': 100}


@pytest.mark.unit
def test_resolve_string_parameter():
    """Test resolving routes with string parameters."""
    router = Router()
    
    def handler(req, username):
        return f"User {username}"
    
    router.add_route("/profile/<str:username>", handler, methods=["GET"], endpoint="profile")
    
    handler_result, params = router.resolve("/profile/john_doe", "GET")
    assert handler_result == handler
    assert params == {'username': 'john_doe'}


@pytest.mark.unit
def test_resolve_path_parameter():
    """Test resolving routes with path parameters (catch-all)."""
    router = Router()
    
    def handler(req, filepath):
        return f"File {filepath}"
    
    router.add_route("/files/<path:filepath>", handler, methods=["GET"], endpoint="file_serve")
    
    handler_result, params = router.resolve("/files/docs/readme.txt", "GET")
    assert handler_result == handler
    assert 'filepath' in params


@pytest.mark.unit
def test_resolve_not_found():
    """Test that resolving non-existent route raises NotFound."""
    from jsweb.routing import NotFound
    
    router = Router()
    
    def handler(req):
        return "OK"
    
    router.add_route("/exists", handler, endpoint="exists")
    
    with pytest.raises(NotFound):
        router.resolve("/does-not-exist", "GET")


@pytest.mark.unit
def test_resolve_wrong_method():
    """Test that route with wrong method raises MethodNotAllowed."""
    from jsweb.routing import MethodNotAllowed
    
    router = Router()
    
    def handler(req):
        return "OK"
    
    router.add_route("/api/data", handler, methods=["POST"], endpoint="create_data")
    
    with pytest.raises(MethodNotAllowed):
        router.resolve("/api/data", "GET")


@pytest.mark.unit
def test_multiple_routes():
    """Test routing with multiple registered routes."""
    router = Router()
    
    def home_handler(req):
        return "Home"
    
    def about_handler(req):
        return "About"
    
    def user_handler(req, user_id):
        return f"User {user_id}"
    
    router.add_route("/", home_handler, methods=["GET"], endpoint="home")
    router.add_route("/about", about_handler, methods=["GET"], endpoint="about")
    router.add_route("/users/<int:user_id>", user_handler, methods=["GET"], endpoint="user")
    
    # Test home route
    handler, params = router.resolve("/", "GET")
    assert handler == home_handler
    assert params == {}
    
    # Test about route
    handler, params = router.resolve("/about", "GET")
    assert handler == about_handler
    assert params == {}
    
    # Test user route
    handler, params = router.resolve("/users/99", "GET")
    assert handler == user_handler
    assert params == {'user_id': 99}


@pytest.mark.unit
def test_route_method_filtering():
    """Test that routes correctly filter by HTTP method."""
    from jsweb.routing import MethodNotAllowed
    router = Router()
    
    def handler(req):
        return "OK"
    
    router.add_route("/api/items", handler, methods=["GET", "POST"], endpoint="items")
    
    # GET should match
    handler_result, _ = router.resolve("/api/items", "GET")
    assert handler_result == handler
    
    # POST should match
    handler_result, _ = router.resolve("/api/items", "POST")
    assert handler_result == handler
    
    # DELETE should not match - raises exception
    with pytest.raises(MethodNotAllowed):
        router.resolve("/api/items", "DELETE")


@pytest.mark.unit
def test_default_methods():
    """Test that routes default to GET method."""
    from jsweb.routing import MethodNotAllowed
    router = Router()
    
    def handler(req):
        return "OK"
    
    router.add_route("/default", handler, endpoint="default")
    
    # Should resolve GET by default
    handler_result, _ = router.resolve("/default", "GET")
    assert handler_result == handler
    
    # POST should not match - raises exception
    with pytest.raises(MethodNotAllowed):
        router.resolve("/default", "POST")


@pytest.mark.slow
def test_static_route_performance():
    """Benchmark static route resolution performance."""
    router = Router()
    
    # Add 50 static routes
    for i in range(50):
        router.add_route(f"/pages/{i}", lambda req: "OK", endpoint=f"page_{i}")
    
    # Resolve middle route 1000 times
    import time
    start = time.perf_counter()
    for _ in range(1000):
        router.resolve("/pages/25", "GET")
    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
    
    # Should be reasonably fast (under 10ms for 1000 requests)
    assert elapsed < 10, f"Static route resolution took {elapsed}ms for 1000 requests"


@pytest.mark.slow
def test_dynamic_route_performance():
    """Benchmark dynamic route resolution performance."""
    router = Router()
    
    # Add 10 dynamic routes
    for i in range(10):
        router.add_route(f"/users/<int:user_id>/posts/<int:post_id>", 
                        lambda req: "OK", endpoint=f"user_post_{i}")
    
    # Resolve 1000 times
    import time
    start = time.perf_counter()
    for _ in range(1000):
        router.resolve("/users/123/posts/456", "GET")
    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
    
    # Should be reasonably fast (under 50ms for 1000 requests)
    assert elapsed < 50, f"Dynamic route resolution took {elapsed}ms for 1000 requests"

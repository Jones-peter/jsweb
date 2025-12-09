"""
Test script to verify Phase 1 routing optimizations work correctly.
"""
from jsweb.routing import Router, NotFound, MethodNotAllowed

def test_static_routes():
    """Test static route optimization"""
    router = Router()

    @router.route("/", methods=["GET"])
    def home():
        return "Home"

    @router.route("/about", methods=["GET", "POST"])
    def about():
        return "About"

    # Test successful resolution
    handler, params = router.resolve("/", "GET")
    assert handler == home
    assert params == {}
    print("[OK] Static route GET /")

    handler, params = router.resolve("/about", "POST")
    assert handler == about
    assert params == {}
    print("[OK] Static route POST /about")

    # Test method not allowed
    try:
        router.resolve("/", "POST")
        assert False, "Should raise MethodNotAllowed"
    except MethodNotAllowed:
        print("[OK] Method not allowed works")

def test_dynamic_routes():
    """Test dynamic route with typed converters"""
    router = Router()

    @router.route("/users/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        return f"User {user_id}"

    @router.route("/posts/<int:post_id>/comments/<int:comment_id>", methods=["GET"])
    def get_comment(post_id, comment_id):
        return f"Post {post_id}, Comment {comment_id}"

    @router.route("/files/<path:filepath>", methods=["GET"])
    def get_file(filepath):
        return f"File {filepath}"

    # Test int converter
    handler, params = router.resolve("/users/123", "GET")
    assert handler == get_user
    assert params == {"user_id": 123}
    assert isinstance(params["user_id"], int)
    print("[OK] Int converter: /users/123 -> user_id=123 (int)")

    # Test negative int
    handler, params = router.resolve("/users/-5", "GET")
    assert params == {"user_id": -5}
    print("[OK] Negative int converter: /users/-5 -> user_id=-5")

    # Test multiple int params
    handler, params = router.resolve("/posts/42/comments/7", "GET")
    assert handler == get_comment
    assert params == {"post_id": 42, "comment_id": 7}
    print("[OK] Multiple int params: /posts/42/comments/7")

    # Test path converter
    handler, params = router.resolve("/files/docs/readme.txt", "GET")
    assert handler == get_file
    assert params == {"filepath": "docs/readme.txt"}
    print("[OK] Path converter: /files/docs/readme.txt")

    # Test invalid int (should not match)
    try:
        router.resolve("/users/abc", "GET")
        assert False, "Should raise NotFound for invalid int"
    except NotFound:
        print("[OK] Invalid int rejected: /users/abc")

def test_url_for():
    """Test reverse URL generation"""
    router = Router()

    @router.route("/", endpoint="home")
    def home():
        return "Home"

    @router.route("/users/<int:user_id>", endpoint="user_detail")
    def user_detail(user_id):
        return f"User {user_id}"

    # Static route
    url = router.url_for("home")
    assert url == "/"
    print("[OK] url_for static: home -> /")

    # Dynamic route
    url = router.url_for("user_detail", user_id=42)
    assert url == "/users/42"
    print("[OK] url_for dynamic: user_detail(user_id=42) -> /users/42")

def test_slots_memory():
    """Verify __slots__ is working"""
    router = Router()

    @router.route("/test", methods=["GET"])
    def test():
        return "Test"

    route = router.static_routes["/test"]

    # __slots__ should prevent adding arbitrary attributes
    try:
        route.some_random_attribute = "value"
        assert False, "__slots__ should prevent new attributes"
    except AttributeError:
        print("[OK] __slots__ working: prevents arbitrary attributes")

if __name__ == "__main__":
    print("Testing Phase 1 Routing Optimizations")
    print("=" * 50)

    test_static_routes()
    print()

    test_dynamic_routes()
    print()

    test_url_for()
    print()

    test_slots_memory()
    print()

    print("=" * 50)
    print("[PASS] All tests passed! Phase 1 optimizations working correctly.")
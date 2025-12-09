import time
import re
from typing import Dict, List

# ========== OLD ROUTING (Unoptimized) ==========
class OldRoute:
    def __init__(self, path, handler, methods, endpoint):
        self.path = path
        self.handler = handler
        self.methods = methods
        self.endpoint = endpoint
        self.converters = {}
        self.regex, self.param_names = self._compile_path()
    
    def _compile_path(self):
        type_converters = {
            'str': (str, r'[^/]+'),
            'int': (int, r'\d+'),
            'path': (str, r'.+?')
        }
        param_defs = re.findall(r"<(\w+):(\w+)>", self.path)
        regex_path = "^" + self.path + "$"
        param_names = []
        for type_name, param_name in param_defs:
            converter, regex_part = type_converters.get(type_name, type_converters['str'])
            regex_path = regex_path.replace(f"<{type_name}:{param_name}>", f"(?P<{param_name}>{regex_part})")
            self.converters[param_name] = converter
            param_names.append(param_name)
        return re.compile(regex_path), param_names
    
    def match(self, path):
        match = self.regex.match(path)
        if not match:
            return None
        params = match.groupdict()
        try:
            for name, value in params.items():
                params[name] = self.converters[name](value)
            return params
        except ValueError:
            return None

class OldRouter:
    def __init__(self):
        self.routes = []
        self.endpoints = {}
    
    def add_route(self, path, handler, methods=None, endpoint=None):
        if methods is None:
            methods = ["GET"]
        if endpoint is None:
            endpoint = handler.__name__
        if endpoint in self.endpoints:
            raise ValueError(f"Endpoint \"{endpoint}\" is already registered.")
        route = OldRoute(path, handler, methods, endpoint)
        self.routes.append(route)
        self.endpoints[endpoint] = route
    
    def resolve(self, path, method):
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                if method in route.methods:
                    return route.handler, params
        return None, None

# ========== NEW ROUTING (Optimized) ==========
from jsweb.routing import Router as NewRouter

# ========== BENCHMARK ==========
def benchmark_comparison():
    print("=" * 60)
    print("ROUTING PERFORMANCE COMPARISON")
    print("=" * 60)
    
    # Setup old router
    old_router = OldRouter()
    for i in range(40):
        old_router.add_route(f"/pages/{i}", lambda req: "OK", methods=["GET"], endpoint=f"old_page_{i}")
    for i in range(10):
        old_router.add_route(f"/users/<int:user_id>/posts/<int:post_id>", 
                           lambda req: "OK", endpoint=f"old_user_post_{i}")
    
    # Setup new router
    new_router = NewRouter()
    for i in range(50):
        new_router.add_route(f"/pages/{i}", lambda req: "OK", methods=["GET"], endpoint=f"new_page_{i}")
    for i in range(10):
        new_router.add_route(f"/users/<int:user_id>/posts/<int:post_id>", 
                           lambda req: "OK", endpoint=f"new_user_post_{i}")
    
    iterations = 100000
    
    # ===== STATIC ROUTE BENCHMARK =====
    print(f"\nSTATIC ROUTE (/pages/25) - {iterations:,} requests")
    print("-" * 60)
    
    # Old router
    start = time.perf_counter()
    for _ in range(iterations):
        old_router.resolve("/pages/25", "GET")
    old_static_ms = (time.perf_counter() - start) * 1000
    
    # New router
    start = time.perf_counter()
    for _ in range(iterations):
        new_router.resolve("/pages/25", "GET")
    new_static_ms = (time.perf_counter() - start) * 1000
    
    static_improvement = ((old_static_ms - new_static_ms) / old_static_ms) * 100
    
    print(f"Old Router:  {old_static_ms:7.2f}ms total | {old_static_ms/iterations*1000:7.4f}μs per request")
    print(f"New Router:  {new_static_ms:7.2f}ms total | {new_static_ms/iterations*1000:7.4f}μs per request")
    print(f"Improvement: {static_improvement:+.1f}% faster")
    print(f"Speedup:     {old_static_ms/new_static_ms:.2f}x")
    
    # ===== DYNAMIC ROUTE BENCHMARK =====
    print(f"\nDYNAMIC ROUTE (/users/123/posts/456) - {iterations:,} requests")
    print("-" * 60)
    
    # Old router
    start = time.perf_counter()
    for _ in range(iterations):
        old_router.resolve("/users/123/posts/456", "GET")
    old_dynamic_ms = (time.perf_counter() - start) * 1000
    
    # New router
    start = time.perf_counter()
    for _ in range(iterations):
        new_router.resolve("/users/123/posts/456", "GET")
    new_dynamic_ms = (time.perf_counter() - start) * 1000
    
    dynamic_improvement = ((old_dynamic_ms - new_dynamic_ms) / old_dynamic_ms) * 100
    
    print(f"Old Router:  {old_dynamic_ms:7.2f}ms total | {old_dynamic_ms/iterations*1000:7.4f}μs per request")
    print(f"New Router:  {new_dynamic_ms:7.2f}ms total | {new_dynamic_ms/iterations*1000:7.4f}μs per request")
    print(f"Improvement: {dynamic_improvement:+.1f}% faster")
    print(f"Speedup:     {old_dynamic_ms/new_dynamic_ms:.2f}x")
    
    # ===== SUMMARY =====
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Static Routes:  {static_improvement:+6.1f}% improvement ({old_static_ms/new_static_ms:.2f}x faster)")
    print(f"Dynamic Routes: {dynamic_improvement:+6.1f}% improvement ({old_dynamic_ms/new_dynamic_ms:.2f}x faster)")
    
    if static_improvement >= 90:
        print(f"\nSUCCESS! Achieved 90%+ improvement on static routes!")
    elif static_improvement >= 50:
        print(f"\nGOOD! Significant performance improvement achieved!")
    else:
        print(f"\nModerate improvement - consider further optimizations")

if __name__ == "__main__":
    benchmark_comparison()
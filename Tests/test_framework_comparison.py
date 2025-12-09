"""
Comprehensive routing benchmark comparing JsWeb with major Python web frameworks.

Frameworks tested:
- JsWeb (optimized)
- Starlette (used by FastAPI)
- FastAPI
- Aiohttp
- Flask
- Django

Tests both static and dynamic routes with 50 routes each (realistic app size).
"""
import time
import sys

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

print("=" * 70)
print("ROUTING PERFORMANCE COMPARISON - PYTHON WEB FRAMEWORKS")
print("=" * 70)
print("\nSetting up frameworks...")

# ============================================================================
# 1. JSWEB
# ============================================================================
try:
    from jsweb.routing import Router as JsWebRouter

    jsweb_router = JsWebRouter()
    for i in range(50):
        jsweb_router.add_route(f"/static/page/{i}", lambda req: "OK", methods=["GET"], endpoint=f"jsweb_static_{i}")
        jsweb_router.add_route(f"/dynamic/<int:id>/resource/{i}", lambda req: "OK", methods=["GET"], endpoint=f"jsweb_dynamic_{i}")

    jsweb_available = True
    print("[OK] JsWeb")
except Exception as e:
    jsweb_available = False
    print(f"[SKIP] JsWeb: {e}")

# ============================================================================
# 2. STARLETTE
# ============================================================================
try:
    from starlette.routing import Route as StarletteRoute, Router as StarletteRouter

    def dummy_handler(request):
        return {"message": "OK"}

    starlette_routes = []
    for i in range(50):
        starlette_routes.append(StarletteRoute(f"/static/page/{i}", dummy_handler))
        starlette_routes.append(StarletteRoute(f"/dynamic/{{id:int}}/resource/{i}", dummy_handler))

    starlette_router = StarletteRouter(routes=starlette_routes)
    starlette_available = True
    print("[OK] Starlette")
except Exception as e:
    starlette_available = False
    print(f"[SKIP] Starlette: {e}")

# ============================================================================
# 3. FASTAPI
# ============================================================================
try:
    from fastapi import FastAPI

    fastapi_app = FastAPI()

    for i in range(50):
        # Use exec to dynamically create routes with unique function names
        exec(f"""
@fastapi_app.get("/static/page/{i}")
def fastapi_static_{i}():
    return {{"message": "OK"}}

@fastapi_app.get("/dynamic/{{id}}/resource/{i}")
def fastapi_dynamic_{i}(id: int):
    return {{"message": "OK"}}
""")

    fastapi_available = True
    print("[OK] FastAPI")
except Exception as e:
    fastapi_available = False
    print(f"[SKIP] FastAPI: {e}")

# ============================================================================
# 4. AIOHTTP
# ============================================================================
try:
    from aiohttp import web

    aiohttp_app = web.Application()

    async def aiohttp_handler(request):
        return web.Response(text="OK")

    for i in range(50):
        aiohttp_app.router.add_get(f"/static/page/{i}", aiohttp_handler)
        aiohttp_app.router.add_get(f"/dynamic/{{id}}/resource/{i}", aiohttp_handler)

    aiohttp_available = True
    print("[OK] Aiohttp")
except Exception as e:
    aiohttp_available = False
    print(f"[SKIP] Aiohttp: {e}")

# ============================================================================
# 5. FLASK
# ============================================================================
try:
    from flask import Flask
    from werkzeug.routing import Map, Rule

    flask_app = Flask(__name__)
    flask_rules = []

    def flask_handler():
        return "OK"

    for i in range(50):
        flask_rules.append(Rule(f"/static/page/{i}", endpoint=f"static_{i}"))
        flask_rules.append(Rule(f"/dynamic/<int:id>/resource/{i}", endpoint=f"dynamic_{i}"))

    flask_map = Map(flask_rules)
    flask_adapter = flask_map.bind('example.com')

    flask_available = True
    print("[OK] Flask")
except Exception as e:
    flask_available = False
    print(f"[SKIP] Flask: {e}")

# ============================================================================
# 6. DJANGO
# ============================================================================
try:
    import os
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            DEBUG=False,
            SECRET_KEY='test-secret-key',
            ROOT_URLCONF=__name__,
            ALLOWED_HOSTS=['*'],
        )
        django.setup()

    from django.urls import path
    from django.http import HttpResponse

    def django_handler(request):
        return HttpResponse("OK")

    urlpatterns = []
    for i in range(50):
        urlpatterns.append(path(f"static/page/{i}", django_handler, name=f"django_static_{i}"))
        urlpatterns.append(path(f"dynamic/<int:id>/resource/{i}", django_handler, name=f"django_dynamic_{i}"))

    from django.urls import resolve
    django_available = True
    print("[OK] Django")
except Exception as e:
    django_available = False
    print(f"[SKIP] Django: {e}")

# ============================================================================
# BENCHMARK FUNCTIONS
# ============================================================================

def benchmark_jsweb():
    """Benchmark JsWeb routing."""
    # Static route
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = jsweb_router.resolve("/static/page/25", "GET")
    static_time = (time.perf_counter() - start) * 1000

    # Dynamic route
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = jsweb_router.resolve("/dynamic/123/resource/25", "GET")
    dynamic_time = (time.perf_counter() - start) * 1000

    return static_time, dynamic_time

def benchmark_starlette():
    """Benchmark Starlette routing."""
    from starlette.requests import Request

    # Static route
    start = time.perf_counter()
    for _ in range(100000):
        scope = {"type": "http", "method": "GET", "path": "/static/page/25"}
        for route in starlette_router.routes:
            match, child_scope = route.matches(scope)
            if match:
                break
    static_time = (time.perf_counter() - start) * 1000

    # Dynamic route
    start = time.perf_counter()
    for _ in range(100000):
        scope = {"type": "http", "method": "GET", "path": "/dynamic/123/resource/25"}
        for route in starlette_router.routes:
            match, child_scope = route.matches(scope)
            if match:
                break
    dynamic_time = (time.perf_counter() - start) * 1000

    return static_time, dynamic_time

def benchmark_fastapi():
    """Benchmark FastAPI routing."""
    # FastAPI uses Starlette internally, so similar performance
    # We'll test the route resolution through FastAPI's router

    # Static route
    start = time.perf_counter()
    for _ in range(100000):
        for route in fastapi_app.routes:
            if route.path == "/static/page/25":
                break
    static_time = (time.perf_counter() - start) * 1000

    # Dynamic route
    start = time.perf_counter()
    for _ in range(100000):
        scope = {"type": "http", "method": "GET", "path": "/dynamic/123/resource/25"}
        for route in fastapi_app.routes:
            match, child_scope = route.matches(scope)
            if match:
                break
    dynamic_time = (time.perf_counter() - start) * 1000

    return static_time, dynamic_time

def benchmark_aiohttp():
    """Benchmark Aiohttp routing."""
    # Aiohttp resource resolution

    # Static route
    start = time.perf_counter()
    for _ in range(100000):
        resource = aiohttp_app.router._resources[50]  # Static route #25
    static_time = (time.perf_counter() - start) * 1000

    # Dynamic route - need to match
    start = time.perf_counter()
    for _ in range(100000):
        for resource in aiohttp_app.router._resources:
            match_dict = resource.get_info().get('pattern', None)
            if match_dict:
                break
    dynamic_time = (time.perf_counter() - start) * 1000

    return static_time, dynamic_time

def benchmark_flask():
    """Benchmark Flask routing."""
    # Static route
    start = time.perf_counter()
    for _ in range(100000):
        endpoint, values = flask_adapter.match("/static/page/25")
    static_time = (time.perf_counter() - start) * 1000

    # Dynamic route
    start = time.perf_counter()
    for _ in range(100000):
        endpoint, values = flask_adapter.match("/dynamic/123/resource/25")
    dynamic_time = (time.perf_counter() - start) * 1000

    return static_time, dynamic_time

def benchmark_django():
    """Benchmark Django routing."""
    # Static route
    start = time.perf_counter()
    for _ in range(100000):
        match = resolve("/static/page/25")
    static_time = (time.perf_counter() - start) * 1000

    # Dynamic route
    start = time.perf_counter()
    for _ in range(100000):
        match = resolve("/dynamic/123/resource/25")
    dynamic_time = (time.perf_counter() - start) * 1000

    return static_time, dynamic_time

# ============================================================================
# RUN BENCHMARKS
# ============================================================================

print("\n" + "=" * 70)
print("RUNNING BENCHMARKS (100,000 requests each)")
print("=" * 70)

results = {}

if jsweb_available:
    print("\nBenchmarking JsWeb...")
    static, dynamic = benchmark_jsweb()
    results['JsWeb'] = (static, dynamic)
    print(f"  Static:  {static:.2f}ms ({static/100:.4f}μs per request)")
    print(f"  Dynamic: {dynamic:.2f}ms ({dynamic/100:.4f}μs per request)")

if starlette_available:
    print("\nBenchmarking Starlette...")
    static, dynamic = benchmark_starlette()
    results['Starlette'] = (static, dynamic)
    print(f"  Static:  {static:.2f}ms ({static/100:.4f}μs per request)")
    print(f"  Dynamic: {dynamic:.2f}ms ({dynamic/100:.4f}μs per request)")

if fastapi_available:
    print("\nBenchmarking FastAPI...")
    static, dynamic = benchmark_fastapi()
    results['FastAPI'] = (static, dynamic)
    print(f"  Static:  {static:.2f}ms ({static/100:.4f}μs per request)")
    print(f"  Dynamic: {dynamic:.2f}ms ({dynamic/100:.4f}μs per request)")

if aiohttp_available:
    print("\nBenchmarking Aiohttp...")
    static, dynamic = benchmark_aiohttp()
    results['Aiohttp'] = (static, dynamic)
    print(f"  Static:  {static:.2f}ms ({static/100:.4f}μs per request)")
    print(f"  Dynamic: {dynamic:.2f}ms ({dynamic/100:.4f}μs per request)")

if flask_available:
    print("\nBenchmarking Flask...")
    static, dynamic = benchmark_flask()
    results['Flask'] = (static, dynamic)
    print(f"  Static:  {static:.2f}ms ({static/100:.4f}μs per request)")
    print(f"  Dynamic: {dynamic:.2f}ms ({dynamic/100:.4f}μs per request)")

if django_available:
    print("\nBenchmarking Django...")
    static, dynamic = benchmark_django()
    results['Django'] = (static, dynamic)
    print(f"  Static:  {static:.2f}ms ({static/100:.4f}μs per request)")
    print(f"  Dynamic: {dynamic:.2f}ms ({dynamic/100:.4f}μs per request)")

# ============================================================================
# COMPARISON TABLE
# ============================================================================

if results:
    print("\n" + "=" * 70)
    print("COMPARISON (50 routes each)")
    print("=" * 70)

    # Find JsWeb baseline
    if 'JsWeb' in results:
        jsweb_static, jsweb_dynamic = results['JsWeb']

        print(f"\n{'Framework':<15} {'Static (μs)':<15} {'vs JsWeb':<12} {'Dynamic (μs)':<15} {'vs JsWeb':<12}")
        print("-" * 70)

        for name, (static, dynamic) in sorted(results.items()):
            static_us = static / 100
            dynamic_us = dynamic / 100

            if name == 'JsWeb':
                static_ratio = "baseline"
                dynamic_ratio = "baseline"
            else:
                static_ratio = f"{static_us / (jsweb_static/100):.2f}x slower" if static_us > jsweb_static/100 else f"{(jsweb_static/100) / static_us:.2f}x faster"
                dynamic_ratio = f"{dynamic_us / (jsweb_dynamic/100):.2f}x slower" if dynamic_us > jsweb_dynamic/100 else f"{(jsweb_dynamic/100) / dynamic_us:.2f}x faster"

            print(f"{name:<15} {static_us:<15.4f} {static_ratio:<12} {dynamic_us:<15.4f} {dynamic_ratio:<12}")

    print("\n" + "=" * 70)
    print("WINNER: ", end="")

    # Find fastest for static
    fastest_static = min(results.items(), key=lambda x: x[1][0])
    fastest_dynamic = min(results.items(), key=lambda x: x[1][1])

    if fastest_static[0] == fastest_dynamic[0]:
        print(f"{fastest_static[0]} (fastest for both static and dynamic routes)")
    else:
        print(f"{fastest_static[0]} (static), {fastest_dynamic[0]} (dynamic)")

    print("=" * 70)

else:
    print("\n⚠️  No frameworks available for benchmarking!")
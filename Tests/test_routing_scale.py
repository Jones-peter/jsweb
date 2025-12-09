"""
Benchmark routing performance with 1000 routes to test scalability.
"""
import time
from jsweb.routing import Router

def benchmark_1000_routes():
    """Test routing performance with 1000 static and 1000 dynamic routes."""
    router = Router()

    print("=" * 60)
    print("ROUTING SCALABILITY TEST - 1000 ROUTES")
    print("=" * 60)

    # Add 1000 static routes
    print("\nSetting up 1000 static routes...")
    for i in range(1000):
        router.add_route(f"/static/page/{i}", lambda req: "OK", methods=["GET"], endpoint=f"static_page_{i}")

    # Add 1000 dynamic routes
    print("Setting up 1000 dynamic routes...")
    for i in range(1000):
        router.add_route(f"/dynamic/<int:id>/resource/{i}", lambda req: "OK", methods=["GET"], endpoint=f"dynamic_resource_{i}")

    print(f"\nTotal routes: {len(router.static_routes)} static + {len(router.dynamic_routes)} dynamic")

    # Benchmark static route - best case (first route)
    print("\n" + "-" * 60)
    print("STATIC ROUTE - BEST CASE (first route)")
    print("-" * 60)
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/static/page/0", "GET")
    best_static_ms = (time.perf_counter() - start) * 1000
    print(f"Time: {best_static_ms:.2f}ms total | {best_static_ms/100:.4f}μs per request")

    # Benchmark static route - worst case (last route)
    print("\n" + "-" * 60)
    print("STATIC ROUTE - WORST CASE (last route)")
    print("-" * 60)
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/static/page/999", "GET")
    worst_static_ms = (time.perf_counter() - start) * 1000
    print(f"Time: {worst_static_ms:.2f}ms total | {worst_static_ms/100:.4f}μs per request")

    # Benchmark static route - middle case
    print("\n" + "-" * 60)
    print("STATIC ROUTE - AVERAGE CASE (middle route)")
    print("-" * 60)
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/static/page/500", "GET")
    avg_static_ms = (time.perf_counter() - start) * 1000
    print(f"Time: {avg_static_ms:.2f}ms total | {avg_static_ms/100:.4f}μs per request")

    # Benchmark dynamic route - best case (first route)
    print("\n" + "-" * 60)
    print("DYNAMIC ROUTE - BEST CASE (first route)")
    print("-" * 60)
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/dynamic/123/resource/0", "GET")
    best_dynamic_ms = (time.perf_counter() - start) * 1000
    print(f"Time: {best_dynamic_ms:.2f}ms total | {best_dynamic_ms/100:.4f}μs per request")

    # Benchmark dynamic route - worst case (last route)
    print("\n" + "-" * 60)
    print("DYNAMIC ROUTE - WORST CASE (last route)")
    print("-" * 60)
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/dynamic/123/resource/999", "GET")
    worst_dynamic_ms = (time.perf_counter() - start) * 1000
    print(f"Time: {worst_dynamic_ms:.2f}ms total | {worst_dynamic_ms/100:.4f}μs per request")

    # Benchmark dynamic route - middle case
    print("\n" + "-" * 60)
    print("DYNAMIC ROUTE - AVERAGE CASE (middle route)")
    print("-" * 60)
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/dynamic/123/resource/500", "GET")
    avg_dynamic_ms = (time.perf_counter() - start) * 1000
    print(f"Time: {avg_dynamic_ms:.2f}ms total | {avg_dynamic_ms/100:.4f}μs per request")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY - 1000 ROUTES EACH")
    print("=" * 60)
    print(f"\nStatic Routes (O(1) dict lookup):")
    print(f"  Best case:    {best_static_ms/100:.4f}μs per request")
    print(f"  Average case: {avg_static_ms/100:.4f}μs per request")
    print(f"  Worst case:   {worst_static_ms/100:.4f}μs per request")

    print(f"\nDynamic Routes (O(n) linear search):")
    print(f"  Best case:    {best_dynamic_ms/100:.4f}μs per request")
    print(f"  Average case: {avg_dynamic_ms/100:.4f}μs per request")
    print(f"  Worst case:   {worst_dynamic_ms/100:.4f}μs per request")

    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)

    # Check if static routes are still O(1)
    if worst_static_ms / best_static_ms < 1.5:
        print("Static routes: O(1) confirmed - no degradation with 1000 routes")
    else:
        print("Static routes: Some performance degradation detected")

    # Check if dynamic routes show linear degradation
    dynamic_ratio = worst_dynamic_ms / best_dynamic_ms
    print(f"\nDynamic routes worst/best ratio: {dynamic_ratio:.2f}x")

    if avg_dynamic_ms / 100 < 10:  # Less than 10 microseconds average
        print("Dynamic routes: Still fast enough (<10μs) - Phase 2 NOT needed")
    elif avg_dynamic_ms / 100 < 50:  # Less than 50 microseconds
        print("Dynamic routes: Acceptable (<50μs) - Phase 2 optional")
    else:
        print("Dynamic routes: Slow (>50μs) - Phase 2 Radix Tree recommended")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    benchmark_1000_routes()
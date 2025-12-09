import time
from jsweb.routing import Router

def benchmark():
    router = Router()

    #Add 40 static routes
    for i in range(40):
        router.add_route(f"/pages/{i}",lambda req: "OK", methods=["GET"], endpoint=f"page_{i}")

    #Add 10 dynamic routes
    for i in range(10):
        router.add_route(f"/users/<int:id>/post/<int:post>", lambda req: "OK", endpoint=f"user_post_{i}")
    
    #Benchmark resolving static routes
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/pages/25", "GET")
    static_ms = (time.perf_counter() - start) * 1000

    #Benchmark resolving dynamic routes
    start = time.perf_counter()
    for _ in range(100000):
        handler, params = router.resolve("/users/123/post/456", "GET")
    dynamic_ms = (time.perf_counter() - start) * 1000

    print(f"Statics: {static_ms:.2f} ms (100k requests) = {static_ms/100:.4f}ms avg")
    print(f"Dynamics: {dynamic_ms:.2f} ms (100k requests) = {dynamic_ms/100:.4f}ms avg")
    print(f"\nPerformance: ~{100 - (static_ms/250)*100:.0f}% improvement for static routes")

if __name__ == "__main__":
    benchmark()

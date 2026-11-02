import time
from functools import wraps

from django.db import connection
from django.test.utils import CaptureQueriesContext


def profile_queries(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        with CaptureQueriesContext(connection) as ctx:
            start = time.perf_counter()
            response = view(request, *args, **kwargs)
            total = time.perf_counter() - start

        db_time = sum(float(q["time"]) for q in ctx.captured_queries)
        print(
            f"\n{view.__name__}: total {total:.3f}s | {len(ctx)} queries | db {db_time:.3f}s"
        )

        slowest = sorted(
            ctx.captured_queries, key=lambda q: float(q["time"]), reverse=True
        )
        for q in slowest[:5]:
            print(f'  {q["time"]}s  {q["sql"][:100]}')

        return response

    return wrapper

"""Benchmark helpers that measure algorithm execution without UI rendering."""
import statistics
import time
from typing import Callable, Any


def measure(run: Callable[[], dict[str, Any]], repeats: int = 5) -> dict[str, Any]:
    if not isinstance(repeats, int) or not 1 <= repeats <= 1000:
        raise ValueError("Repeats must be between 1 and 1000")
    durations, result = [], None
    for _ in range(repeats):
        start = time.perf_counter()
        result = run()
        durations.append(time.perf_counter() - start)
    return {"result": result, "samples_seconds": durations, "median_seconds": statistics.median(durations),
            "min_seconds": min(durations), "max_seconds": max(durations), "repeats": repeats}

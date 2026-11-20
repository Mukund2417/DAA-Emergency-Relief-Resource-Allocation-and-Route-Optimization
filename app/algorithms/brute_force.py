"""Small-input exhaustive baselines for sorting and TSP."""
from itertools import permutations
from typing import Any


def tsp(matrix: list[list[float | None]], start: int = 0) -> dict[str, Any]:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix) or not 0 <= start < n:
        raise ValueError("Expected a square non-empty distance matrix and valid start")
    best, best_tour, checked = float("inf"), [], 0
    for tail in permutations([v for v in range(n) if v != start]):
        tour = (start,) + tail + (start,); cost = 0.0; valid = True
        for a, b in zip(tour, tour[1:]):
            edge = matrix[a][b]
            if edge is None: valid = False; break
            cost += edge
        checked += 1
        if valid and cost < best: best, best_tour = cost, list(tour)
    return {"tour": best_tour, "cost": best, "operations": checked}


def quadratic_sort(values: list[Any]) -> dict[str, Any]:
    result, comparisons = list(values), 0
    for i in range(1, len(result)):
        value, j = result[i], i
        while j > 0:
            comparisons += 1
            if result[j - 1] <= value: break
            result[j] = result[j - 1]; j -= 1
        result[j] = value
    return {"sorted": result, "operations": comparisons}

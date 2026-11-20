"""Full-table 0/1 Knapsack dynamic programming and exhaustive baseline."""
from typing import Any


def solve(items: list[tuple[str, int, int]], capacity: int) -> dict[str, Any]:
    _validate(items, capacity)
    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    events, operations = [], 0
    for i, (name, weight, value) in enumerate(items, 1):
        for cap in range(capacity + 1):
            excluded = dp[i - 1][cap]
            included = value + dp[i - 1][cap - weight] if weight <= cap else -1
            dp[i][cap] = max(excluded, included)
            operations += 1
            events.append({"item_index": i, "capacity": cap, "include": included >= excluded,
                           "value": dp[i][cap]})
    selected, cap = [], capacity
    for i in range(n, 0, -1):
        if dp[i][cap] != dp[i - 1][cap]:
            name, weight, value = items[i - 1]
            selected.append({"name": name, "weight": weight, "value": value})
            cap -= weight
    selected.reverse()
    return {"value": dp[n][capacity], "weight": sum(x["weight"] for x in selected),
            "items": selected, "table": dp, "events": events, "operations": operations}


def brute_force(items: list[tuple[str, int, int]], capacity: int) -> dict[str, Any]:
    _validate(items, capacity)
    best_value, best_mask, checked = 0, 0, 0
    for mask in range(1 << len(items)):
        checked += 1
        weight = sum(items[i][1] for i in range(len(items)) if mask >> i & 1)
        value = sum(items[i][2] for i in range(len(items)) if mask >> i & 1)
        if weight <= capacity and value > best_value:
            best_value, best_mask = value, mask
    chosen = [items[i] for i in range(len(items)) if best_mask >> i & 1]
    return {"value": best_value, "weight": sum(x[1] for x in chosen),
            "items": [{"name": n, "weight": w, "value": v} for n, w, v in chosen],
            "operations": checked}


def _validate(items: list[tuple[str, int, int]], capacity: int) -> None:
    if not isinstance(capacity, int) or capacity < 0:
        raise ValueError("Capacity must be a non-negative integer")
    if any(not isinstance(w, int) or w <= 0 or not isinstance(v, int) or v < 0 for _, w, v in items):
        raise ValueError("Weights must be positive integers and values non-negative integers")

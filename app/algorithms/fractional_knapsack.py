"""Greedy fractional knapsack with deterministic sorting and decision events."""
from dataclasses import dataclass
from math import isfinite
from typing import Any
from app.algorithms.merge_sort import sort as merge_sort


@dataclass(frozen=True)
class Item:
    name: str
    weight: float
    value: float


def solve(items: list[Item], capacity: float) -> dict[str, Any]:
    if not isfinite(capacity) or capacity < 0:
        raise ValueError("Capacity must be a finite non-negative number")
    if any(not isfinite(i.weight) or i.weight <= 0 for i in items):
        raise ValueError("Every item weight must be finite and greater than zero")
    if any(not isfinite(i.value) or i.value < 0 for i in items):
        raise ValueError("Every item value must be finite and non-negative")
    ordering = merge_sort(list(enumerate(items)), key=lambda pair: -pair[1].value / pair[1].weight,
                          capture_events=False)
    ordered = ordering["sorted"]
    remaining, total, chosen, events = capacity, 0.0, [], []
    for _, item in ordered:
        if remaining <= 0:
            break
        fraction = min(1.0, remaining / item.weight)
        used = item.weight * fraction
        gain = item.value * fraction
        remaining -= used
        total += gain
        chosen.append({"name": item.name, "fraction": fraction, "weight": used, "value": gain})
        events.append({"item": item.name, "fraction": fraction, "remaining": remaining, "value": total})
    return {"value": total, "weight": capacity - remaining, "items": chosen,
            "events": events, "sort_comparisons": ordering["comparisons"],
            "operations": ordering["comparisons"] + len(events)}

"""Bellman-Ford shortest paths with reachable negative-cycle detection."""
import math
from typing import Any


def solve(vertices: list[str], edges: list[tuple[str, str, float]], source: str) -> dict[str, Any]:
    if source not in vertices: raise ValueError("Source must be a graph vertex")
    known = set(vertices)
    if len(known) != len(vertices): raise ValueError("Vertex names must be unique")
    if any(a not in known or b not in known or not math.isfinite(w) for a, b, w in edges):
        raise ValueError("Edges must reference known vertices and have finite weights")
    dist, prev, events, operations = {v: math.inf for v in vertices}, {v: None for v in vertices}, [], 0
    dist[source] = 0.0
    for _ in range(max(0, len(vertices) - 1)):
        changed = False
        for a, b, weight in edges:
            operations += 1
            if dist[a] != math.inf and dist[a] + weight < dist[b]:
                old = dist[b]; dist[b], prev[b], changed = dist[a] + weight, a, True
                events.append({"edge": (a, b), "old": old, "new": dist[b]})
        if not changed: break
    for a, b, weight in edges:
        if dist[a] != math.inf and dist[a] + weight < dist[b]:
            raise ValueError("Reachable negative-weight cycle detected")
    return {"distances": dist, "previous": prev, "events": events, "operations": operations}

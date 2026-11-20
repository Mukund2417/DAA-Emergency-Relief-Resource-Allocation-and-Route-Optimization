"""Dijkstra shortest paths using adjacency lists and heapq."""
import heapq
import math
from typing import Any


def solve(graph: dict[str, list[tuple[str, float]]], source: str, target: str | None = None) -> dict[str, Any]:
    if source not in graph or (target is not None and target not in graph):
        raise ValueError("Source and destination must be graph vertices")
    for edges in graph.values():
        for neighbor, weight in edges:
            if neighbor not in graph: raise ValueError(f"Unknown vertex: {neighbor}")
            if not math.isfinite(weight) or weight < 0: raise ValueError("Dijkstra requires finite non-negative edge weights")
    dist, prev = {v: math.inf for v in graph}, {v: None for v in graph}
    dist[source], queue, events, visited, operations = 0.0, [(0.0, source)], [], [], 0
    settled = set()
    while queue:
        distance, vertex = heapq.heappop(queue)
        if vertex in settled or distance != dist[vertex]: continue
        settled.add(vertex); visited.append(vertex)
        events.append({"type": "visit", "vertex": vertex, "distance": distance})
        if vertex == target: break
        for neighbor, weight in graph[vertex]:
            operations += 1
            candidate = distance + weight
            if candidate < dist[neighbor]:
                old = dist[neighbor]; dist[neighbor], prev[neighbor] = candidate, vertex
                heapq.heappush(queue, (candidate, neighbor))
                events.append({"type": "relax", "edge": (vertex, neighbor), "old": old, "new": candidate})
    path, cursor = [], target
    if target is not None and math.isfinite(dist[target]):
        while cursor is not None:
            path.append(cursor)
            if cursor == source: break
            cursor = prev[cursor]
        path.reverse()
    return {"distances": dist, "previous": prev, "path": path, "cost": dist[target] if target else None,
            "visited": visited, "events": events, "operations": operations}

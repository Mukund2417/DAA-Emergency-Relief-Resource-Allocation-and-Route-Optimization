"""Exact branch-and-bound TSP for small finite non-negative cost matrices.

For symmetric costs, the admissible bound uses cheapest endpoint connections and
an MST over unvisited vertices. For asymmetric costs, it uses an outgoing-edge
relaxation: a cheapest next edge from the endpoint plus each unvisited vertex's
cheapest outgoing edge to another remaining vertex or the start. That relaxation
cannot overestimate a valid completion.
"""
import math
from typing import Any


def solve(matrix: list[list[float | None]], start: int = 0) -> dict[str, Any]:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix): raise ValueError("Distance matrix must be non-empty and square")
    if not 0 <= start < n: raise ValueError("Starting vertex is out of range")
    symmetric = True
    for i in range(n):
        for j in range(n):
            w = matrix[i][j]
            if w is not None and (not math.isfinite(w) or w < 0): raise ValueError("TSP requires finite non-negative weights")
            if w != matrix[j][i]: symmetric = False
    if n == 1: return {"tour": [start, start], "cost": 0.0, "expanded": 0, "pruned": 0, "events": []}
    best_cost, best_tour, expanded, pruned, events = math.inf, [], 0, 0, []

    def mst_cost(nodes: set[int]) -> float:
        if len(nodes) <= 1: return 0.0
        root = next(iter(nodes)); reached, total = {root}, 0.0
        while reached != nodes:
            choice = min(((matrix[a][b], b) for a in reached for b in nodes - reached if matrix[a][b] is not None), default=(math.inf, -1))
            if not math.isfinite(choice[0]): return math.inf
            total += choice[0]; reached.add(choice[1])
        return total

    def bound(path: list[int], cost: float) -> float:
        unvisited = set(range(n)) - set(path)
        if not unvisited:
            back = matrix[path[-1]][start]
            return cost + (back if back is not None else math.inf)
        if not symmetric:
            first = min((matrix[path[-1]][v] for v in unvisited if matrix[path[-1]][v] is not None), default=math.inf)
            rest = 0.0
            for vertex in unvisited:
                outgoing = min((matrix[vertex][v] for v in (unvisited - {vertex}) | {start}
                                if matrix[vertex][v] is not None), default=math.inf)
                rest += outgoing
            return cost + first + rest
        left = min((matrix[path[-1]][v] for v in unvisited if matrix[path[-1]][v] is not None), default=math.inf)
        right = min((matrix[v][start] for v in unvisited if matrix[v][start] is not None), default=math.inf)
        return cost + left + right + mst_cost(unvisited)

    def visit(path: list[int], cost: float) -> None:
        nonlocal best_cost, best_tour, expanded, pruned
        current_bound = bound(path, cost)
        if current_bound >= best_cost:
            pruned += 1; events.append({"path": path[:], "bound": current_bound, "action": "prune"}); return
        if len(path) == n:
            closing = matrix[path[-1]][start]
            if closing is not None and cost + closing < best_cost:
                best_cost, best_tour = cost + closing, path + [start]
                events.append({"path": best_tour[:], "bound": best_cost, "action": "best"})
            return
        expanded += 1
        events.append({"path": path[:], "bound": current_bound, "action": "expand"})
        for nxt in range(n):
            edge = matrix[path[-1]][nxt]
            if nxt not in path and edge is not None:
                visit(path + [nxt], cost + edge)

    visit([start], 0.0)
    return {"tour": best_tour, "cost": best_cost, "expanded": expanded, "pruned": pruned, "events": events}

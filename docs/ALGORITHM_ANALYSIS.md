# Algorithm Analysis

Let `n` be item/value count, `W` an integer knapsack capacity, `V` graph vertices, `E` directed edges, and `k` TSP locations. The space column describes core auxiliary state and excludes instrumented event histories, which consume additional space proportional to recorded events.

| Algorithm | Best case | Average case | Worst case | Auxiliary space |
|---|---:|---:|---:|---:|
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| Fractional Knapsack, with ratio sorting | O(n log n) | O(n log n) | O(n log n) | O(n) |
| 0/1 Knapsack full DP table | O(nW) | O(nW) | O(nW) | O(nW) |
| Dijkstra, adjacency list + binary heap | O((V+E) log V) | O((V+E) log V) | O((V+E) log V) | O(V) algorithm state, O(V+E) including graph |
| Bellman-Ford with early exit | O(E) | O(VE) | O(VE) | O(V) beyond graph |
| TSP Branch and Bound | Bound/input dependent | Bound/input dependent | O(k!) | O(k) recursion plus search log; worst-case log can be exponential |
| Exhaustive TSP | O(k!) | O(k!) | O(k!) | O(k) per permutation |
| Insertion Sort baseline | O(n) | O(n²) | O(n²) | O(1) extra |

The 0/1 DP is pseudo-polynomial because its runtime depends on the numeric W, not only the number of bits used to encode W. Fractional and 0/1 Knapsack are distinct formulations.

## Pseudocode summaries

### Merge Sort
```text
sort(A):
  if length(A) <= 1: return A
  split A into L and R
  return stable_merge(sort(L), sort(R))
```

### Fractional Knapsack
```text
stable-sort supplies by descending value / weight
for supply in order:
  take min(1, remaining_capacity / supply.weight)
  add proportional value and used capacity
```

### 0/1 Knapsack
```text
DP[0][c] = 0
for item i = 1..n:
  for c = 0..W:
    DP[i][c] = max(DP[i-1][c], value[i] + DP[i-1][c-weight[i]]) if it fits
trace DP rows backward to reconstruct selected whole items
```

### Dijkstra
```text
dist[source] = 0; all others = infinity; push source in min-heap
while heap not empty:
  extract minimum unsettled vertex u
  for each outgoing edge (u,v,w):
    if dist[u] + w < dist[v]: update dist[v], predecessor[v], and heap
```

### Bellman-Ford
```text
repeat at most V-1 times:
  relax each edge; stop if no distance changed
scan edges once more; a reachable improvement means a negative cycle
```

### TSP Branch and Bound
```text
search(path, cost):
  lower_bound = admissible_completion_bound(path, cost)
  if lower_bound >= incumbent: prune
  else if all locations visited: close tour and update incumbent
  else recursively append each unvisited reachable location
```

For symmetric non-negative TSP costs the implementation uses current cost + cheapest endpoint connection + MST over unvisited nodes + cheapest return connection. The MST is no more expensive than the completion's internal connection path. For asymmetric costs, it uses a directed outgoing-edge relaxation: cheapest next edge from the current endpoint plus an independently cheapest outgoing edge from every unvisited vertex to another unvisited vertex or the start. Every completion must pay one such outgoing edge per term, so the relaxation is admissible. Exact worst-case time remains factorial; the UI/API limit is ten nodes.

## Reproducible measurement method

`backend/app/services/benchmark_service.py` generates deterministic data with `random.Random(seed)`, performs one unrecorded warm-up, then records repeated `time.perf_counter()` durations and median/mean. Input size, seed, count, Python version and platform are persisted. The algorithm runs outside chart rendering. Operation counters are algorithm-specific and do not represent a universal unit of work.

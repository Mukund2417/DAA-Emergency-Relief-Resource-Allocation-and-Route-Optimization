# Algorithm Explanations

## Merge Sort

Split the list in half until each sublist contains at most one value, recursively sort both halves, and stably merge them. The merge chooses the left element first when keys compare equal. Sorting uses O(n log n) comparisons in best, average and worst cases, and O(n) working storage. The optional event log adds storage proportional to its recorded steps.

## Fractional Knapsack

For each divisible supply, compute value per unit weight. Stable Merge Sort orders supplies by descending ratio. Take full supplies while capacity permits and a fraction of the next supply when only part fits. Sorting costs O(n log n), selection O(n), and the total remains O(n log n) with O(n) working storage. A first-fit input-order baseline demonstrates how order affects a simple policy. This greedy proof does not extend to indivisible packages.

## 0/1 Knapsack

For item prefix i and integer capacity c, store the better of excluding item i and including it plus the best previous state at capacity c - weight_i. Trace the full table backward to recover the selected packages. The implementation costs O(nW) time and O(nW) table space. It is pseudo-polynomial because W is a numeric value. The exhaustive comparator enumerates all 2^n subsets and is used only on small cases.

## Dijkstra

Store directed roads in adjacency lists. Use a min-heap to settle the next smallest tentative distance, then relax outgoing edges. Stale heap entries are skipped. Distances and predecessors reconstruct a shortest route; unreachable vertices retain an unbounded distance and are serialized as null at the API boundary. Negative weights are rejected. With adjacency lists and a binary heap, time is O((V+E) log V); graph storage is O(V+E) and algorithm state O(V), plus the heap.

## Bellman-Ford

Relax all directed edges for up to V-1 passes, stopping early when a pass changes no distance. A final pass checks for a reachable negative cycle. Time is O(VE), with O(V) distance/predecessor state beyond the edge list. This supports negative edges, unlike Dijkstra.

## TSP Branch and Bound

Extend partial tours recursively, maintain the best complete tour and prune when a valid lower bound cannot beat it. For a symmetric matrix, the lower bound is current path cost plus a cheapest connection from the current endpoint to the unvisited set, an MST connecting the unvisited vertices, and a cheapest return connection to the start. For asymmetric matrices, the lower bound relaxes degree constraints: cheapest next edge from the endpoint plus each remaining vertex's cheapest outgoing edge to a remaining vertex or the start. Every completion must include one such outgoing edge for each term, so summing independent minima cannot exceed the completion cost. The exact worst-case time remains O(n!); the search event log can be exponential. The API caps matrices at 10 nodes.

## Experimental comparisons

- Merge Sort vs insertion-sort baseline use identical values.
- Fractional Knapsack vs first-fit use identical divisible items and capacity.
- 0/1 DP vs exhaustive enumeration use identical whole items and capacity.
- Dijkstra vs Bellman-Ford use the same non-negative saved graph.
- Branch and Bound vs exhaustive TSP use the same cost matrix and start node.

Measured time uses `time.perf_counter` around algorithm execution only. Theoretical bounds and observed timings answer different questions and are shown separately.

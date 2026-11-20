# Viva Questions and Answers

## Merge Sort

1. **What is divide and conquer?** Divide an input into smaller instances, solve those recursively, then combine their answers.
2. **What are Merge Sort's three stages?** Divide the list, recursively sort each half, and merge both sorted halves.
3. **Why is the merge stable?** When equal keys are compared, the implementation takes the item from the left half first.
4. **What is its recurrence?** `T(n)=2T(n/2)+O(n)`.
5. **Why is the time O(n log n)?** There are O(log n) split levels and O(n) merge work per level.
6. **What auxiliary storage does it need?** O(n) for temporary merge arrays, excluding optional event history.
7. **Does this implementation sort in place?** No; it copies each pair of halves while merging.
8. **What are best, average and worst time bounds?** O(n log n) for each for the standard implementation.
9. **What baseline is used?** Insertion Sort on the exact same input list.
10. **How are duplicate values handled?** Stable ordering preserves the original relative order of equal keys.

## Fractional Knapsack

1. **What does fractional mean?** An item can be taken in a partial quantity.
2. **What ratio determines order?** Objective value divided by item weight/cost.
3. **Why is the greedy choice optimal here?** For divisible items, replacing lower ratio capacity with higher ratio capacity cannot reduce objective value.
4. **What are its time and space bounds?** O(n log n) time including sort and O(n) auxiliary storage.
5. **What is selected last when capacity runs out?** A fraction of the next ranked item.
6. **Why reject zero weight?** Value/weight ratio would be undefined.
7. **Why is this not a solution to 0/1 Knapsack?** 0/1 items cannot be divided; the greedy ratio proof no longer holds.
8. **What is first-fit comparison?** It consumes items in supplied input order, using identical items and capacity.
9. **How is leftover capacity computed?** Start at the input capacity and subtract each selected quantity times its weight.
10. **What does equal ratio do?** Stable sorting provides deterministic order without changing the optimal objective.

## 0/1 Knapsack

1. **What does 0/1 represent?** Each item is either selected completely or not selected.
2. **What is the DP state?** Best value from the first i items at capacity c.
3. **What is the recurrence?** Maximum of excluding item i or its value plus the previous state at remaining capacity.
4. **Why is the capacity integer?** The table indexes discrete capacity states from 0 to W.
5. **What are time and space bounds?** O(nW) time and O(nW) for the full table.
6. **Why call it pseudo-polynomial?** Runtime depends on numeric W, which can be large relative to its bit length.
7. **How are selected items recovered?** Trace table rows backward and detect where including the item improved the state.
8. **What is the brute-force baseline?** Enumerate all 2^n subsets and keep the best feasible set.
9. **Why can ratio greedy fail?** A high ratio small item may prevent choosing a combination with higher total value.
10. **How is correctness checked on small input?** Compare the DP objective value with exhaustive enumeration for the same input.

## Dijkstra

1. **What does Dijkstra solve?** Shortest paths from one source when all edge weights are non-negative.
2. **What graph representation is used?** Adjacency lists of outgoing neighbors and weights.
3. **What does relaxation mean?** Test whether reaching v through u improves its tentative distance.
4. **Why use a min-heap?** It efficiently exposes the smallest tentative distance next.
5. **Why reject negative edges?** A later negative edge can make a previously settled route shorter and invalidate the greedy property.
6. **What does infinity mean in the output?** The vertex is unreachable from the source.
7. **How is a path reconstructed?** Store predecessors on distance improvements and walk them backward from the target.
8. **What is the common heap complexity?** O((V+E) log V) with adjacency lists and a binary heap.
9. **What does Bellman-Ford add?** It supports negative edges and detects reachable negative cycles, at O(VE) time.
10. **Are the edges directed?** Yes. Add a reverse edge when a road is usable in both directions.

## TSP Branch and Bound

1. **What is a TSP tour?** A cycle that visits each selected vertex once and returns to its starting depot.
2. **What is a search node?** A partial tour considered by the search.
3. **What is the incumbent?** The best complete tour cost found so far.
4. **What does the lower bound represent?** A cost no greater than any completion of that partial tour.
5. **When can a branch be pruned?** When its lower bound is at least the incumbent.
6. **Why is the symmetric bound admissible?** Every completion needs endpoint connections and an internal spanning connection; an MST is no more expensive than that internal path.
7. **How is the asymmetric bound formed?** Add the cheapest next edge from the endpoint and a cheapest possible outgoing edge for every remaining vertex; this relaxes edge conflicts, so it cannot overestimate.
8. **What is the worst-case runtime?** O(n!); many branches may avoid pruning.
9. **How is the result validated?** Compare its cost with exhaustive permutation enumeration on small matrices.
10. **Why limit the interface to ten nodes?** Exact search can grow factorially, and the lower bound does not guarantee polynomial-time behavior.

## Bellman-Ford comparison

1. **How does it differ from Dijkstra?** It allows negative edges; Dijkstra does not.
2. **How many relaxation passes are needed?** At most V-1 complete passes for shortest simple paths.
3. **Why can it stop early?** If a full pass makes no changes, later passes cannot improve distances.
4. **How detect a negative cycle?** A reachable edge still improves after V-1 passes.
5. **What is its worst-case time?** O(VE).
6. **What storage does it use?** O(V) distance/predecessor state beyond the graph.
7. **Does it detect every negative cycle?** It detects cycles reachable from the selected source.
8. **Why compare on non-negative graphs?** Then both methods solve the same shortest-path instance and distances can be checked directly.
9. **What does an unreachable vertex retain?** Infinity internally; the API serializes it as null.
10. **Can Bellman-Ford be faster on all graphs?** No; its worst-case work is generally higher, though early termination may help some inputs.

## System, database, measurements and team

1. **Why is the algorithm code separate from FastAPI?** The same module is easier to unit-test and the API remains a transport layer.
2. **What does SQLite provide?** Local relational persistence without requiring a separate database server.
3. **How are database relationships enforced?** Foreign keys and column checks are enabled for each connection.
4. **How does the frontend call Dijkstra?** It sends a request to FastAPI; Python computes the authoritative path.
5. **What does React Flow do?** It renders and edits saved graph node/edge data; it does not compute routes.
6. **What does Recharts display?** Actual saved benchmark measurements returned by the API.
7. **How are benchmark inputs made reproducible?** A fixed seed initializes Python's random generator.
8. **Why do we warm up before measuring?** The first execution can include initialization effects and is excluded from recorded samples.
9. **Why distinguish measured and theoretical complexity?** Runtime depends on hardware, implementation and input; asymptotic bounds describe growth.
10. **What are the major limitations?** Manual static data, no live traffic/maps, no multi-vehicle optimization, small exact TSP cap, and no emergency dispatch validation.
11. **What is the status of the college format?** The named guideline PDF was not supplied; it must be checked before printing.
12. **How should members describe contributions?** Each student should state verified work, then explain the complete system and their assigned module.

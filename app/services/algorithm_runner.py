"""JSON-friendly dispatcher shared by the GUI and benchmark page."""
from app.algorithms import fractional_knapsack, zero_one_knapsack, merge_sort, dijkstra, bellman_ford, tsp_branch_bound, brute_force


def run(name: str, data: dict):
    if name == "Fractional Knapsack":
        items = [fractional_knapsack.Item(**item) for item in data["items"]]
        return fractional_knapsack.solve(items, data["capacity"])
    if name == "0/1 Knapsack": return zero_one_knapsack.solve(data["items"], data["capacity"])
    if name == "0/1 Knapsack (brute force)": return zero_one_knapsack.brute_force(data["items"], data["capacity"])
    if name == "Merge Sort": return merge_sort.sort(data["values"])
    if name == "Insertion Sort baseline": return brute_force.quadratic_sort(data["values"])
    if name == "Dijkstra": return dijkstra.solve(data["graph"], data["source"], data.get("target"))
    if name == "Bellman-Ford": return bellman_ford.solve(data["vertices"], data["edges"], data["source"])
    if name == "TSP Branch and Bound": return tsp_branch_bound.solve(data["matrix"], data.get("start", 0))
    if name == "TSP exhaustive": return brute_force.tsp(data["matrix"], data.get("start", 0))
    raise ValueError(f"Unknown algorithm: {name}")

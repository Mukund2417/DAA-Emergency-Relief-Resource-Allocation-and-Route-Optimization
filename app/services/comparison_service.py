"""Fair same-input comparisons requested in the DAA project brief."""
import time
from app.services.algorithm_runner import run


PAIRS = {
    "0/1 Knapsack": ("0/1 Knapsack", "0/1 Knapsack (brute force)"),
    "Shortest paths": ("Dijkstra", "Bellman-Ford"),
    "TSP": ("TSP Branch and Bound", "TSP exhaustive"),
    "Sorting": ("Merge Sort", "Insertion Sort baseline"),
}


def compare(category: str, data: dict) -> dict:
    if category not in PAIRS: raise ValueError("Choose one of: 0/1 Knapsack, Shortest paths, TSP, Sorting")
    names = PAIRS[category]
    inputs = [data, data]
    if category == "Shortest paths":
        graph = data["graph"]
        inputs = [data, {"vertices": list(graph), "edges": [(u,v,w) for u,edges in graph.items() for v,w in edges], "source":data["source"]}]
    outputs, elapsed = [], []
    for name, inp in zip(names,inputs):
        start=time.perf_counter(); outputs.append(run(name,inp)); elapsed.append(time.perf_counter()-start)
    if category == "Shortest paths":
        equivalent = all(outputs[0]["distances"][v] == outputs[1]["distances"][v] for v in data["graph"])
    elif category == "Sorting": equivalent = outputs[0]["sorted"] == outputs[1]["sorted"]
    else: equivalent = outputs[0]["value"] == outputs[1]["value"] if category == "0/1 Knapsack" else outputs[0]["cost"] == outputs[1]["cost"]
    return {"category":category,"algorithms":list(names),"outputs":outputs,"elapsed_seconds":elapsed,"same_optimum":equivalent}

"""Calls the original algorithms and records measured, data-backed runs."""
import json
import math
import time
from typing import Any
from backend.app.algorithms import merge_sort, fractional_knapsack, knapsack_01, dijkstra, bellman_ford, tsp_branch_bound


def json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value): return None
    if isinstance(value, dict): return {str(k): json_safe(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [json_safe(v) for v in value]
    return value


def execute(name: str, data: dict) -> dict:
    if name == "merge_sort": return merge_sort.sort(data["values"], key=data.get("key"))
    if name == "fractional_knapsack":
        items=[fractional_knapsack.Item(**item) for item in data["items"]]
        return fractional_knapsack.solve(items,data["capacity"])
    if name in ("knapsack_01","knapsack_01_bruteforce"):
        items=data["items"]; capacity=data["capacity"]
        if len(items)>25 and name.endswith("bruteforce"): raise ValueError("Exhaustive 0/1 comparison is limited to 25 items.")
        if name=="knapsack_01" and (not isinstance(capacity,int) or capacity<0 or (len(items)+1)*(capacity+1)>250000):
            raise ValueError("DP visualization requires non-negative integer capacity and is limited to 250,000 table cells.")
        return knapsack_01.solve(items,capacity) if name=="knapsack_01" else knapsack_01.brute_force(items,capacity)
    if name == "dijkstra":
        graph=data["graph"]
        if len(graph)>3000 or sum(map(len,graph.values()))>100000: raise ValueError("Dijkstra input is limited to 3,000 vertices and 100,000 directed edges.")
        return dijkstra.solve(graph,data["source"],data.get("target"))
    if name == "bellman_ford": return bellman_ford.solve(data["vertices"],data["edges"],data["source"])
    if name == "tsp_branch_bound":
        if len(data["matrix"]) > 10: raise ValueError("The exact TSP explorer is limited to 10 locations.")
        return tsp_branch_bound.solve(data["matrix"],data.get("start",0))
    if name == "tsp_bruteforce":
        if len(data["matrix"]) > 10: raise ValueError("The exhaustive TSP comparison is limited to 10 locations.")
        from app.algorithms.brute_force import tsp
        return tsp(data["matrix"],data.get("start",0))
    if name == "insertion_sort_baseline":
        from app.algorithms.brute_force import quadratic_sort
        return quadratic_sort(data["values"])
    raise ValueError(f"Unsupported algorithm: {name}")


def measured(name: str, data: dict) -> tuple[dict, float]:
    start=time.perf_counter(); output=execute(name,data); elapsed=time.perf_counter()-start
    return json_safe(output),elapsed


def operation_count(output: dict) -> int:
    for key in ("operations","expanded","comparisons"):
        if isinstance(output.get(key),int): return output[key]
    return 0


def save_run(con, name: str, data: dict, output: dict, elapsed: float, scenario_id=None) -> int:
    cur=con.execute("INSERT INTO algorithm_runs(scenario_id,algorithm,input_json,output_json,elapsed_seconds,operations) VALUES(?,?,?,?,?,?)",
        (scenario_id,name,json.dumps(json_safe(data)),json.dumps(output),elapsed,operation_count(output)))
    run_id=cur.lastrowid
    if "knapsack" in name or "fractional" in name:
        con.execute("INSERT INTO allocation_results(run_id,result_json) VALUES(?,?)",(run_id,json.dumps(output)))
    if "dijkstra" in name or "bellman" in name or "tsp" in name:
        con.execute("INSERT INTO route_results(run_id,result_json) VALUES(?,?)",(run_id,json.dumps(output)))
    return int(run_id)

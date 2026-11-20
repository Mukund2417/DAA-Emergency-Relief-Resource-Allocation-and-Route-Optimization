"""Fixed-seed benchmark datasets and repeated execution measurements."""
import random
import statistics
import platform
import sys
import time
from typing import Any
from backend.app.services.algorithm_service import execute, json_safe


def dataset(name: str, n: int, seed: int) -> dict[str,Any]:
    rng=random.Random(seed)
    if name in ("merge_sort","insertion_sort_baseline"):
        if name=="insertion_sort_baseline" and n>5000: raise ValueError("Insertion-sort baseline is limited to 5,000 values.")
        return {"values":[rng.randrange(-10000,10001) for _ in range(n)]}
    if name=="fractional_knapsack":
        if n>3000: raise ValueError("Fractional Knapsack benchmark is limited to 3,000 items.")
        return {"capacity":float(n*10),"items":[{"name":f"Supply {i+1}","weight":rng.randrange(1,100),"value":rng.randrange(1,1000)} for i in range(n)]}
    if name in ("knapsack_01","knapsack_01_bruteforce"):
        if n>25: raise ValueError("0/1 benchmark is limited to 25 items; exhaustive comparisons grow exponentially.")
        return {"capacity":max(1,n*10),"items":[[f"Package {i+1}",rng.randrange(1,30),rng.randrange(1,100)] for i in range(n)]}
    if name=="dijkstra":
        if n>300: raise ValueError("Graph benchmark is limited to 300 vertices.")
        graph={f"L{i}":[] for i in range(n)}
        for i in range(max(0,n-1)):
            w=rng.randrange(1,100); graph[f"L{i}"].append((f"L{i+1}",w)); graph[f"L{i+1}"].append((f"L{i}",w))
        for _ in range(n*2):
            if n<3: break
            a,b=rng.sample(range(n),2); w=rng.randrange(1,100)
            graph[f"L{a}"].append((f"L{b}",w)); graph[f"L{b}"].append((f"L{a}",w))
        return {"graph":graph,"source":"L0","target":f"L{n-1}"}
    if name=="tsp_branch_bound":
        if n>10: raise ValueError("TSP benchmark is limited to 10 vertices.")
        matrix=[[None if i==j else rng.randrange(1,100) for j in range(n)] for i in range(n)]
        for i in range(n):
            for j in range(i): matrix[i][j]=matrix[j][i]
        return {"matrix":matrix,"start":0}
    raise ValueError(f"No reproducible dataset generator for: {name}")


def run_benchmark(name: str, n: int, seed: int, repeats: int) -> dict:
    data=dataset(name,n,seed)
    execute(name,data)  # warm-up is not included in recorded samples
    samples=[]; output=None
    for _ in range(repeats):
        start=time.perf_counter(); output=execute(name,data); samples.append(time.perf_counter()-start)
    return {"algorithm":name,"input_size":n,"seed":seed,"repeat_count":repeats,
            "measurements_seconds":samples,"median_seconds":statistics.median(samples),
            "mean_seconds":statistics.mean(samples),"python_version":sys.version.split()[0],
            "platform":platform.platform(),"output":json_safe(output)}

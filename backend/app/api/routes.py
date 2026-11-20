"""Scenario, network, algorithm, benchmark and report API."""
import csv
import io
import json
import sqlite3
import time
from typing import Iterator
from fastapi import APIRouter, Depends, HTTPException, Response
from backend.app.models.database import connect
from backend.app.models.schemas import ScenarioIn, LocationIn, ResourceIn, DemandIn, RoadNodeIn, RoadEdgeIn, AlgorithmInput, BenchmarkInput
from backend.app.services.algorithm_service import measured, save_run
from backend.app.services.benchmark_service import run_benchmark
from backend.app.algorithms.dijkstra import solve as dijkstra_solve

router=APIRouter()


def db() -> Iterator[sqlite3.Connection]:
    con=connect()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback(); raise
    finally: con.close()


def row_dict(row): return dict(row) if row else None


def ensure_scenario(con, scenario_id: int):
    if not con.execute("SELECT 1 FROM disaster_scenarios WHERE id=?",(scenario_id,)).fetchone():
        raise HTTPException(404,"Scenario not found")


def run_algorithm(name: str, body: AlgorithmInput, con):
    try:
        if name in ("dijkstra","bellman_ford") and "graph_id" in body.input:
            graph_id=body.input.pop("graph_id")
            ensure_scenario(con,graph_id)
            if body.scenario_id is not None and body.scenario_id!=graph_id:
                raise HTTPException(422,"Route graph and saved run must use the same scenario")
            graph=network_data(con,graph_id)
            if name=="dijkstra":
                body.input["graph"]={v:[] for v in graph["vertices"]}
                for edge in graph["edges"]:
                    if not edge["blocked"]: body.input["graph"][edge["source"]].append((edge["target"],edge["distance"]))
            else:
                body.input["vertices"]=graph["vertices"]
                body.input["edges"]=[(e["source"],e["target"],e["distance"]) for e in graph["edges"] if not e["blocked"]]
        output,elapsed=measured(name,body.input)
        if body.scenario_id is not None: ensure_scenario(con,body.scenario_id)
        run_id=save_run(con,name,body.input,output,elapsed,body.scenario_id)
        return {"run_id":run_id,"algorithm":name,"input":body.input,"output":output,"elapsed_seconds":elapsed}
    except KeyError as exc: raise HTTPException(422,f"Missing input field: {exc.args[0]}") from exc
    except (ValueError,TypeError,IndexError) as exc: raise HTTPException(422,str(exc)) from exc


@router.get("/health")
def health(): return {"status":"ok","service":"Emergency Relief DAA API"}


@router.get("/dashboard")
def dashboard(con=Depends(db)):
    scenario=con.execute("SELECT * FROM disaster_scenarios WHERE status='Active' ORDER BY id DESC LIMIT 1").fetchone()
    counts={"scenarios":con.execute("SELECT COUNT(*) FROM disaster_scenarios").fetchone()[0],
        "locations":con.execute("SELECT COUNT(*) FROM affected_locations").fetchone()[0],
        "resources":con.execute("SELECT COUNT(*) FROM resource_inventory").fetchone()[0],
        "runs":con.execute("SELECT COUNT(*) FROM algorithm_runs").fetchone()[0]}
    recent=[dict(r) for r in con.execute("SELECT id,algorithm,elapsed_seconds,operations,created_at FROM algorithm_runs ORDER BY id DESC LIMIT 8")]
    latest=[dict(r) for r in con.execute("SELECT id,algorithm,input_size,repeat_count,median_seconds,created_at FROM benchmark_runs ORDER BY id DESC LIMIT 8")]
    return {"active_scenario":row_dict(scenario),"counts":counts,"recent_runs":recent,"benchmarks":latest}


@router.get("/scenarios")
def list_scenarios(con=Depends(db)):
    return [dict(r) for r in con.execute("SELECT s.*,COUNT(l.id) location_count FROM disaster_scenarios s LEFT JOIN affected_locations l ON l.scenario_id=s.id GROUP BY s.id ORDER BY s.id DESC")]


@router.post("/scenarios",status_code=201)
def create_scenario(body: ScenarioIn,con=Depends(db)):
    cur=con.execute("INSERT INTO disaster_scenarios(name,scenario_type,description,status) VALUES(?,?,?,?)",(body.name.strip(),body.scenario_type,body.description,body.status))
    return row_dict(con.execute("SELECT * FROM disaster_scenarios WHERE id=?",(cur.lastrowid,)).fetchone())


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id:int,con=Depends(db)):
    row=con.execute("SELECT * FROM disaster_scenarios WHERE id=?",(scenario_id,)).fetchone()
    if not row: raise HTTPException(404,"Scenario not found")
    return dict(row)


@router.put("/scenarios/{scenario_id}")
def update_scenario(scenario_id:int,body:ScenarioIn,con=Depends(db)):
    cur=con.execute("UPDATE disaster_scenarios SET name=?,scenario_type=?,description=?,status=? WHERE id=?",(body.name.strip(),body.scenario_type,body.description,body.status,scenario_id))
    if not cur.rowcount: raise HTTPException(404,"Scenario not found")
    return dict(con.execute("SELECT * FROM disaster_scenarios WHERE id=?",(scenario_id,)).fetchone())


@router.delete("/scenarios/{scenario_id}",status_code=204)
def delete_scenario(scenario_id:int,con=Depends(db)):
    cur=con.execute("DELETE FROM disaster_scenarios WHERE id=?",(scenario_id,))
    if not cur.rowcount: raise HTTPException(404,"Scenario not found")
    return Response(status_code=204)


@router.get("/scenarios/{scenario_id}/locations")
def locations(scenario_id:int,con=Depends(db)):
    ensure_scenario(con,scenario_id)
    return [dict(r) for r in con.execute("SELECT l.* FROM affected_locations l WHERE l.scenario_id=? ORDER BY l.priority DESC,l.name",(scenario_id,))]


@router.post("/locations",status_code=201)
def create_location(body:LocationIn,con=Depends(db)):
    ensure_scenario(con,body.scenario_id)
    try:
        cur=con.execute("INSERT INTO affected_locations(scenario_id,identifier,name,priority,latitude,longitude,x,y) VALUES(?,?,?,?,?,?,?,?)",
            (body.scenario_id,body.identifier,body.name.strip(),body.priority,body.latitude,body.longitude,body.x,body.y))
    except sqlite3.IntegrityError as exc: raise HTTPException(409,"Location name already exists in this scenario") from exc
    for resource,quantity in body.demands.items():
        if quantity<0: raise HTTPException(422,"Demand quantities must be non-negative")
        r=con.execute("SELECT id FROM resource_types WHERE name=?",(resource,)).fetchone()
        if not r: raise HTTPException(422,f"Unknown resource type: {resource}")
        con.execute("INSERT INTO location_demands(location_id,resource_type_id,quantity) VALUES(?,?,?)",(cur.lastrowid,r["id"],quantity))
    return dict(con.execute("SELECT * FROM affected_locations WHERE id=?",(cur.lastrowid,)).fetchone())


@router.put("/locations/{location_id}")
def update_location(location_id:int,body:LocationIn,con=Depends(db)):
    ensure_scenario(con,body.scenario_id)
    cur=con.execute("UPDATE affected_locations SET scenario_id=?,identifier=?,name=?,priority=?,latitude=?,longitude=?,x=?,y=? WHERE id=?",
        (body.scenario_id,body.identifier,body.name.strip(),body.priority,body.latitude,body.longitude,body.x,body.y,location_id))
    if not cur.rowcount: raise HTTPException(404,"Location not found")
    con.execute("DELETE FROM location_demands WHERE location_id=?",(location_id,))
    for resource,quantity in body.demands.items():
        if quantity<0: raise HTTPException(422,"Demand quantities must be non-negative")
        r=con.execute("SELECT id FROM resource_types WHERE name=?",(resource,)).fetchone()
        if not r: raise HTTPException(422,f"Unknown resource type: {resource}")
        con.execute("INSERT INTO location_demands(location_id,resource_type_id,quantity) VALUES(?,?,?)",(location_id,r["id"],quantity))
    return dict(con.execute("SELECT * FROM affected_locations WHERE id=?",(location_id,)).fetchone())


@router.delete("/locations/{location_id}",status_code=204)
def delete_location(location_id:int,con=Depends(db)):
    cur=con.execute("DELETE FROM affected_locations WHERE id=?",(location_id,))
    if not cur.rowcount: raise HTTPException(404,"Location not found")
    return Response(status_code=204)


@router.get("/locations/{location_id}/demands")
def location_demands(location_id:int,con=Depends(db)):
    if not con.execute("SELECT 1 FROM affected_locations WHERE id=?",(location_id,)).fetchone(): raise HTTPException(404,"Location not found")
    return [dict(r) for r in con.execute("SELECT d.*,rt.name resource,rt.unit FROM location_demands d JOIN resource_types rt ON rt.id=d.resource_type_id WHERE d.location_id=? ORDER BY rt.name",(location_id,))]


@router.put("/locations/{location_id}/demands")
def set_location_demand(location_id:int,body:DemandIn,con=Depends(db)):
    if not con.execute("SELECT 1 FROM affected_locations WHERE id=?",(location_id,)).fetchone(): raise HTTPException(404,"Location not found")
    if not con.execute("SELECT 1 FROM resource_types WHERE id=?",(body.resource_type_id,)).fetchone(): raise HTTPException(404,"Resource type not found")
    con.execute("INSERT INTO location_demands(location_id,resource_type_id,quantity) VALUES(?,?,?) ON CONFLICT(location_id,resource_type_id) DO UPDATE SET quantity=excluded.quantity",(location_id,body.resource_type_id,body.quantity))
    return {"location_id":location_id,**body.model_dump()}


@router.delete("/locations/{location_id}/demands/{resource_type_id}",status_code=204)
def delete_location_demand(location_id:int,resource_type_id:int,con=Depends(db)):
    cur=con.execute("DELETE FROM location_demands WHERE location_id=? AND resource_type_id=?",(location_id,resource_type_id))
    if not cur.rowcount: raise HTTPException(404,"Location demand not found")
    return Response(status_code=204)


@router.get("/inventory")
def inventory(scenario_id:int|None=None,con=Depends(db)):
    if scenario_id is not None: ensure_scenario(con,scenario_id)
    where="WHERE ri.scenario_id IS NULL" if scenario_id is None else "WHERE ri.scenario_id IS NULL OR ri.scenario_id=?"
    args=() if scenario_id is None else (scenario_id,)
    return [dict(r) for r in con.execute(f"SELECT ri.id,ri.scenario_id,rt.id resource_type_id,rt.name,rt.category,rt.unit,rt.unit_weight,rt.divisible,rt.value_score,ri.available FROM resource_inventory ri JOIN resource_types rt ON rt.id=ri.resource_type_id {where} ORDER BY rt.category,rt.name",args)]


@router.post("/inventory",status_code=201)
def create_resource(body:ResourceIn,con=Depends(db)):
    if body.scenario_id is not None: ensure_scenario(con,body.scenario_id)
    con.execute("INSERT INTO resource_types(name,category,unit,unit_weight,divisible,value_score) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET category=excluded.category,unit=excluded.unit,unit_weight=excluded.unit_weight,divisible=excluded.divisible,value_score=excluded.value_score",
        (body.name.strip(),body.category,body.unit,body.unit_weight,int(body.divisible),body.value_score))
    resource_id=con.execute("SELECT id FROM resource_types WHERE name=?",(body.name.strip(),)).fetchone()[0]
    cur=con.execute("INSERT INTO resource_inventory(scenario_id,resource_type_id,available) VALUES(?,?,?) ON CONFLICT(scenario_id,resource_type_id) DO UPDATE SET available=excluded.available",
        (body.scenario_id,resource_id,body.available))
    return {"id":resource_id,"scenario_id":body.scenario_id,"name":body.name,"category":body.category,"unit":body.unit,"unit_weight":body.unit_weight,"divisible":body.divisible,"value_score":body.value_score,"available":body.available}


@router.put("/inventory/{resource_type_id}")
def update_resource(resource_type_id:int,body:ResourceIn,con=Depends(db)):
    if body.scenario_id is not None: ensure_scenario(con,body.scenario_id)
    cur=con.execute("UPDATE resource_types SET name=?,category=?,unit=?,unit_weight=?,divisible=?,value_score=? WHERE id=?",
        (body.name.strip(),body.category,body.unit,body.unit_weight,int(body.divisible),body.value_score,resource_type_id))
    if not cur.rowcount: raise HTTPException(404,"Resource type not found")
    stock=con.execute("SELECT 1 FROM resource_inventory WHERE scenario_id IS ? AND resource_type_id=?",(body.scenario_id,resource_type_id)).fetchone()
    if stock: con.execute("UPDATE resource_inventory SET available=? WHERE scenario_id IS ? AND resource_type_id=?",(body.available,body.scenario_id,resource_type_id))
    else: con.execute("INSERT INTO resource_inventory(scenario_id,resource_type_id,available) VALUES(?,?,?)",(body.scenario_id,resource_type_id,body.available))
    return {"id":resource_type_id,**body.model_dump()}


@router.delete("/inventory/{resource_type_id}",status_code=204)
def delete_resource(resource_type_id:int,con=Depends(db)):
    if con.execute("SELECT 1 FROM location_demands WHERE resource_type_id=?",(resource_type_id,)).fetchone():
        raise HTTPException(409,"Remove this resource from location demands before deleting its type")
    con.execute("DELETE FROM resource_inventory WHERE resource_type_id=?",(resource_type_id,))
    cur=con.execute("DELETE FROM resource_types WHERE id=?",(resource_type_id,))
    if not cur.rowcount: raise HTTPException(404,"Resource type not found")
    return Response(status_code=204)


@router.get("/scenarios/{scenario_id}/network")
def network(scenario_id:int,con=Depends(db)):
    ensure_scenario(con,scenario_id)
    return network_data(con,scenario_id)


def network_data(con,scenario_id):
    nodes=[dict(r) for r in con.execute("SELECT * FROM road_nodes WHERE scenario_id=? ORDER BY id",(scenario_id,))]
    edges=[dict(r) for r in con.execute("SELECT e.*,a.name source,b.name target FROM road_edges e JOIN road_nodes a ON a.id=e.source_id JOIN road_nodes b ON b.id=e.target_id WHERE e.scenario_id=? ORDER BY e.id",(scenario_id,))]
    return {"scenario_id":scenario_id,"vertices":[n["name"] for n in nodes],"nodes":nodes,"edges":edges}


@router.post("/road-nodes",status_code=201)
def create_road_node(body:RoadNodeIn,con=Depends(db)):
    ensure_scenario(con,body.scenario_id)
    if body.location_id is not None and not con.execute("SELECT 1 FROM affected_locations WHERE id=? AND scenario_id=?",(body.location_id,body.scenario_id)).fetchone():
        raise HTTPException(422,"Linked location must belong to this scenario")
    try: cur=con.execute("INSERT INTO road_nodes(scenario_id,location_id,name,x,y) VALUES(?,?,?,?,?)",(body.scenario_id,body.location_id,body.name.strip(),body.x,body.y))
    except sqlite3.IntegrityError as exc: raise HTTPException(409,"Road node name already exists in this scenario") from exc
    return dict(con.execute("SELECT * FROM road_nodes WHERE id=?",(cur.lastrowid,)).fetchone())


@router.put("/road-nodes/{node_id}")
def update_road_node(node_id:int,body:RoadNodeIn,con=Depends(db)):
    ensure_scenario(con,body.scenario_id)
    if body.location_id is not None and not con.execute("SELECT 1 FROM affected_locations WHERE id=? AND scenario_id=?",(body.location_id,body.scenario_id)).fetchone():
        raise HTTPException(422,"Linked location must belong to this scenario")
    cur=con.execute("UPDATE road_nodes SET scenario_id=?,location_id=?,name=?,x=?,y=? WHERE id=?",(body.scenario_id,body.location_id,body.name.strip(),body.x,body.y,node_id))
    if not cur.rowcount: raise HTTPException(404,"Road node not found")
    return dict(con.execute("SELECT * FROM road_nodes WHERE id=?",(node_id,)).fetchone())


@router.delete("/road-nodes/{node_id}",status_code=204)
def delete_road_node(node_id:int,con=Depends(db)):
    cur=con.execute("DELETE FROM road_nodes WHERE id=?",(node_id,))
    if not cur.rowcount: raise HTTPException(404,"Road node not found")
    return Response(status_code=204)


@router.post("/road-edges",status_code=201)
def create_road_edge(body:RoadEdgeIn,con=Depends(db)):
    ensure_scenario(con,body.scenario_id)
    endpoint_count=con.execute("SELECT COUNT(*) FROM road_nodes WHERE scenario_id=? AND id IN (?,?)",(body.scenario_id,body.source_id,body.target_id)).fetchone()[0]
    if endpoint_count!=2: raise HTTPException(422,"Both edge endpoints must be distinct nodes in the selected scenario")
    try: cur=con.execute("INSERT INTO road_edges(scenario_id,source_id,target_id,distance,blocked) VALUES(?,?,?,?,?)",(body.scenario_id,body.source_id,body.target_id,body.distance,int(body.blocked)))
    except sqlite3.IntegrityError as exc: raise HTTPException(422,"Edge endpoints must be distinct nodes in the scenario; directed edge may already exist") from exc
    return dict(con.execute("SELECT * FROM road_edges WHERE id=?",(cur.lastrowid,)).fetchone())


@router.post("/road-edges/bidirectional",status_code=201)
def create_bidirectional_road(body:RoadEdgeIn,con=Depends(db)):
    """Create or update both directions as one request."""
    ensure_scenario(con,body.scenario_id)
    endpoint_count=con.execute("SELECT COUNT(*) FROM road_nodes WHERE scenario_id=? AND id IN (?,?)",(body.scenario_id,body.source_id,body.target_id)).fetchone()[0]
    if endpoint_count!=2: raise HTTPException(422,"Choose two different road nodes in the selected scenario")
    for source_id,target_id in ((body.source_id,body.target_id),(body.target_id,body.source_id)):
        con.execute("INSERT INTO road_edges(scenario_id,source_id,target_id,distance,blocked) VALUES(?,?,?,?,?) ON CONFLICT(scenario_id,source_id,target_id) DO UPDATE SET distance=excluded.distance,blocked=excluded.blocked",(body.scenario_id,source_id,target_id,body.distance,int(body.blocked)))
    return [dict(row) for row in con.execute("SELECT * FROM road_edges WHERE scenario_id=? AND ((source_id=? AND target_id=?) OR (source_id=? AND target_id=?)) ORDER BY source_id",(body.scenario_id,body.source_id,body.target_id,body.target_id,body.source_id))]


@router.put("/road-edges/{edge_id}")
def update_road_edge(edge_id:int,body:RoadEdgeIn,con=Depends(db)):
    ensure_scenario(con,body.scenario_id)
    endpoint_count=con.execute("SELECT COUNT(*) FROM road_nodes WHERE scenario_id=? AND id IN (?,?)",(body.scenario_id,body.source_id,body.target_id)).fetchone()[0]
    if endpoint_count!=2: raise HTTPException(422,"Both edge endpoints must be distinct nodes in the selected scenario")
    cur=con.execute("UPDATE road_edges SET scenario_id=?,source_id=?,target_id=?,distance=?,blocked=? WHERE id=?",(body.scenario_id,body.source_id,body.target_id,body.distance,int(body.blocked),edge_id))
    if not cur.rowcount: raise HTTPException(404,"Road edge not found")
    return dict(con.execute("SELECT * FROM road_edges WHERE id=?",(edge_id,)).fetchone())


@router.delete("/road-edges/{edge_id}",status_code=204)
def delete_road_edge(edge_id:int,con=Depends(db)):
    cur=con.execute("DELETE FROM road_edges WHERE id=?",(edge_id,))
    if not cur.rowcount: raise HTTPException(404,"Road edge not found")
    return Response(status_code=204)


@router.post("/algorithms/merge-sort")
def merge_sort_run(body:AlgorithmInput,con=Depends(db)): return run_algorithm("merge_sort",body,con)
@router.post("/algorithms/fractional-knapsack")
def fractional_run(body:AlgorithmInput,con=Depends(db)): return run_algorithm("fractional_knapsack",body,con)
@router.post("/algorithms/knapsack-01")
def knapsack_run(body:AlgorithmInput,con=Depends(db)): return run_algorithm("knapsack_01",body,con)
@router.post("/algorithms/dijkstra")
def dijkstra_run(body:AlgorithmInput,con=Depends(db)): return run_algorithm("dijkstra",body,con)
@router.post("/algorithms/bellman-ford")
def bellman_run(body:AlgorithmInput,con=Depends(db)): return run_algorithm("bellman_ford",body,con)
@router.post("/algorithms/tsp")
def tsp_run(body:AlgorithmInput,con=Depends(db)): return run_algorithm("tsp_branch_bound",body,con)
@router.post("/algorithms/compare/knapsack-01")
def knapsack_compare(body:AlgorithmInput,con=Depends(db)):
    base=run_algorithm("knapsack_01",body,con); brute=run_algorithm("knapsack_01_bruteforce",body,con)
    return {"dynamic_programming":base,"exhaustive":brute,"same_optimum":base["output"]["value"]==brute["output"]["value"]}
@router.post("/algorithms/compare/tsp")
def tsp_compare(body:AlgorithmInput,con=Depends(db)):
    exact=run_algorithm("tsp_branch_bound",body,con); brute=run_algorithm("tsp_bruteforce",body,con)
    return {"branch_and_bound":exact,"exhaustive":brute,"same_optimum":exact["output"]["cost"]==brute["output"]["cost"]}


def network_tour_input(con,scenario_id:int,data:dict):
    ensure_scenario(con,scenario_id)
    graph=network_data(con,scenario_id)
    selected=data.get("vertices",[]); start_name=data.get("start")
    if not 2<=len(selected)<=10: raise HTTPException(422,"Choose 2 to 10 distinct network nodes, including the depot")
    if len(set(selected))!=len(selected) or start_name not in selected: raise HTTPException(422,"Tour nodes must be unique and include the selected depot")
    if any(name not in graph["vertices"] for name in selected): raise HTTPException(422,"Every tour selection must be a saved road node in the scenario")
    adjacency={v:[] for v in graph["vertices"]}
    for edge in graph["edges"]:
        if not edge["blocked"]: adjacency[edge["source"]].append((edge["target"],edge["distance"]))
    matrix=[]
    for source in selected:
        distances=dijkstra_solve(adjacency,source)["distances"]
        matrix.append([None if source==target or distances[target]==float("inf") else distances[target] for target in selected])
    return {"matrix":matrix,"start":selected.index(start_name),"vertices":selected,"depot":start_name}


@router.post("/algorithms/tsp/network")
def network_tsp_run(body:AlgorithmInput,con=Depends(db)):
    scenario_id=body.scenario_id or body.input.get("graph_id")
    if scenario_id is None: raise HTTPException(422,"Select a scenario road network")
    data=network_tour_input(con,scenario_id,body.input)
    try: output,elapsed=measured("tsp_branch_bound",data)
    except (ValueError,KeyError,TypeError) as exc: raise HTTPException(422,str(exc)) from exc
    if output["tour"]: output["tour_names"]=[data["vertices"][i] for i in output["tour"]]
    output["matrix"]=data["matrix"]
    run_id=save_run(con,"tsp_branch_bound",data,output,elapsed,scenario_id)
    return {"run_id":run_id,"algorithm":"tsp_branch_bound","input":data,"output":output,"elapsed_seconds":elapsed}


@router.post("/algorithms/compare/tsp/network")
def network_tsp_compare(body:AlgorithmInput,con=Depends(db)):
    scenario_id=body.scenario_id or body.input.get("graph_id")
    if scenario_id is None: raise HTTPException(422,"Select a scenario road network")
    data=network_tour_input(con,scenario_id,body.input)
    exact_output,exact_time=measured("tsp_branch_bound",data)
    brute_output,brute_time=measured("tsp_bruteforce",data)
    if exact_output["tour"]: exact_output["tour_names"]=[data["vertices"][i] for i in exact_output["tour"]]
    if brute_output["tour"]: brute_output["tour_names"]=[data["vertices"][i] for i in brute_output["tour"]]
    exact_id=save_run(con,"tsp_branch_bound",data,exact_output,exact_time,scenario_id)
    brute_id=save_run(con,"tsp_bruteforce",data,brute_output,brute_time,scenario_id)
    return {"branch_and_bound":{"run_id":exact_id,"output":exact_output,"elapsed_seconds":exact_time},
        "exhaustive":{"run_id":brute_id,"output":brute_output,"elapsed_seconds":brute_time},
        "same_optimum":exact_output["cost"]==brute_output["cost"]}


@router.post("/algorithms/compare/shortest-paths")
def shortest_path_compare(body:AlgorithmInput,con=Depends(db)):
    data=dict(body.input)
    if "graph_id" in data:
        graph_id=data.pop("graph_id"); ensure_scenario(con,graph_id)
        if body.scenario_id is not None and body.scenario_id!=graph_id: raise HTTPException(422,"Route graph and saved run must use the same scenario")
        graph=network_data(con,graph_id)
        adjacency={v:[] for v in graph["vertices"]}
        for edge in graph["edges"]:
            if not edge["blocked"]: adjacency[edge["source"]].append((edge["target"],edge["distance"]))
    else: adjacency=data["graph"]
    edges=[[a,b,w] for a,neighbors in adjacency.items() for b,w in neighbors]
    dijkstra_result=run_algorithm("dijkstra",AlgorithmInput(scenario_id=body.scenario_id,input={"graph":adjacency,"source":data["source"],"target":data.get("target")}),con)
    bellman_result=run_algorithm("bellman_ford",AlgorithmInput(scenario_id=body.scenario_id,input={"vertices":list(adjacency),"edges":edges,"source":data["source"]}),con)
    same=all(dijkstra_result["output"]["distances"][v]==bellman_result["output"]["distances"][v] for v in adjacency)
    return {"dijkstra":dijkstra_result,"bellman_ford":bellman_result,"same_distances":same}


@router.post("/algorithms/compare/merge-sort")
def merge_sort_compare(body:AlgorithmInput,con=Depends(db)):
    merge=run_algorithm("merge_sort",body,con)
    baseline=run_algorithm("insertion_sort_baseline",body,con)
    return {"merge_sort":merge,"insertion_sort":baseline,"same_sorted_output":merge["output"]["sorted"]==baseline["output"]["sorted"]}


@router.post("/algorithms/compare/fractional-knapsack")
def fractional_compare(body:AlgorithmInput,con=Depends(db)):
    greedy=run_algorithm("fractional_knapsack",body,con)
    data=body.input; capacity=data["capacity"]; remaining=capacity; selected=[]; total=0.0
    start=time.perf_counter()
    for item in data["items"]:
        if remaining<=0: break
        fraction=min(1.0,remaining/item["weight"]); weight=item["weight"]*fraction; value=item["value"]*fraction
        remaining-=weight; total+=value; selected.append({"name":item["name"],"fraction":fraction,"weight":weight,"value":value})
    elapsed=time.perf_counter()-start
    baseline={"items":selected,"weight":capacity-remaining,"value":total,"operations":len(selected),"strategy":"first-fit input order"}
    run_id=save_run(con,"fractional_first_fit_baseline",data,baseline,elapsed,body.scenario_id)
    baseline_result={"run_id":run_id,"algorithm":"fractional_first_fit_baseline","output":baseline,"elapsed_seconds":elapsed}
    return {"greedy":greedy,"first_fit_baseline":baseline_result,"same_optimum":greedy["output"]["value"]==baseline["value"]}


@router.post("/benchmarks")
def benchmark(body:BenchmarkInput,con=Depends(db)):
    try: result=run_benchmark(body.algorithm,body.input_size,body.seed,body.repeats)
    except (ValueError,KeyError) as exc: raise HTTPException(422,str(exc)) from exc
    cur=con.execute("INSERT INTO benchmark_runs(algorithm,input_size,seed,repeat_count,median_seconds,python_version,platform) VALUES(?,?,?,?,?,?,?)",
        (result["algorithm"],result["input_size"],result["seed"],result["repeat_count"],result["median_seconds"],result["python_version"],result["platform"]))
    for i,seconds in enumerate(result["measurements_seconds"],1):
        con.execute("INSERT INTO benchmark_measurements(benchmark_id,repetition,elapsed_seconds) VALUES(?,?,?)",(cur.lastrowid,i,seconds))
    result["benchmark_id"]=cur.lastrowid
    return result


@router.get("/benchmarks")
def list_benchmarks(con=Depends(db)):
    return [dict(r) for r in con.execute("SELECT * FROM benchmark_runs ORDER BY id DESC LIMIT 200")]


@router.get("/runs")
def runs(con=Depends(db)):
    return [{**dict(r),"input":json.loads(r["input_json"]),"output":json.loads(r["output_json"])} for r in con.execute("SELECT * FROM algorithm_runs ORDER BY id DESC LIMIT 200")]


@router.get("/reports/{scenario_id}.csv")
def report_csv(scenario_id:int,con=Depends(db)):
    ensure_scenario(con,scenario_id)
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(["run_id","algorithm","measured_seconds","operations","created_at","output_json"])
    for row in con.execute("SELECT id,algorithm,elapsed_seconds,operations,created_at,output_json FROM algorithm_runs WHERE scenario_id=? ORDER BY id",(scenario_id,)):
        writer.writerow(tuple(row))
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=scenario-{scenario_id}-results.csv"})


def basic_pdf(lines:list[str])->bytes:
    """Create a compact one-page A4 PDF without optional native PDF dependencies."""
    import re
    commands=["BT","/F1 10 Tf","48 790 Td","14 TL"]
    for line in lines[:48]:
        safe=re.sub(r"[^\x20-\x7e]","?",line).replace("\\","\\\\").replace("(","\\(").replace(")","\\)")
        commands.append(f"({safe[:105]}) Tj T* ")
    commands.append("ET"); stream="\n".join(commands).encode("ascii")
    objs=[b"<< /Type /Catalog /Pages 2 0 R >>",b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "+str(len(stream)).encode()+b" >>\nstream\n"+stream+b"\nendstream"]
    pdf=bytearray(b"%PDF-1.4\n"); offsets=[0]
    for i,obj in enumerate(objs,1): offsets.append(len(pdf)); pdf.extend(f"{i} 0 obj\n".encode()+obj+b"\nendobj\n")
    xref=len(pdf); pdf.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]: pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)


@router.get("/reports/{scenario_id}.pdf")
def report_pdf(scenario_id:int,con=Depends(db)):
    scenario=con.execute("SELECT * FROM disaster_scenarios WHERE id=?",(scenario_id,)).fetchone()
    if not scenario: raise HTTPException(404,"Scenario not found")
    runs=list(con.execute("SELECT algorithm,elapsed_seconds,operations,created_at FROM algorithm_runs WHERE scenario_id=? ORDER BY id DESC",(scenario_id,)))
    lines=["Emergency Relief DAA - Scenario Report",f"Scenario: {scenario['name']}",f"Type/status: {scenario['scenario_type']} / {scenario['status']}",
        "Academic decision-support prototype. Sample/manual data only; not an emergency dispatch system.","","Saved algorithm executions:"]
    lines += [f"{r['created_at']} | {r['algorithm']} | {r['elapsed_seconds']:.8f} sec | {r['operations']} operations" for r in runs] or ["No algorithm runs are saved for this scenario."]
    return Response(basic_pdf(lines),media_type="application/pdf",headers={"Content-Disposition":f"attachment; filename=scenario-{scenario_id}-report.pdf"})

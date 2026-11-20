"""Synchronous route-function checks; the hosted sandbox blocks asyncio socketpair."""
import pytest
from fastapi import HTTPException
from backend.app.api import routes
from backend.app.models import database
from backend.app.models.schemas import ScenarioIn, LocationIn, ResourceIn, RoadNodeIn, RoadEdgeIn, AlgorithmInput, BenchmarkInput
from backend.app.main import app


def setup_db(tmp_path,monkeypatch):
    monkeypatch.setattr(database,"DATABASE_PATH",tmp_path/"api.db")
    database.initialize()
    return database.connect()


def test_scenario_crud_algorithm_and_reports(tmp_path,monkeypatch):
    con=setup_db(tmp_path,monkeypatch)
    try:
        assert routes.health()["status"]=="ok"
        created=routes.create_scenario(ScenarioIn(name="Monsoon sample",scenario_type="Flood",description="Synthetic case",status="Active"),con)
        scenario_id=created["id"]
        location=routes.create_location(LocationIn(scenario_id=scenario_id,name="Ward 7",priority=5),con)
        assert location["name"]=="Ward 7"
        assert routes.locations(scenario_id,con)[0]["name"]=="Ward 7"
        result=routes.knapsack_run(AlgorithmInput(scenario_id=scenario_id,input={"capacity":5,"items":[["water",3,8],["kit",4,10]]}),con)
        assert result["output"]["value"]==10
        assert routes.runs(con)[0]["algorithm"]=="knapsack_01"
        assert routes.report_csv(scenario_id,con).body.startswith(b"run_id,algorithm")
        assert routes.report_pdf(scenario_id,con).body.startswith(b"%PDF-1.4")
        routes.delete_scenario(scenario_id,con)
        assert routes.list_scenarios(con)==[]
    finally: con.close()


def test_validation_and_graph_algorithm(tmp_path,monkeypatch):
    con=setup_db(tmp_path,monkeypatch)
    try:
        with pytest.raises(HTTPException) as err:
            routes.dijkstra_run(AlgorithmInput(input={"graph":{"A":[["B",-1]],"B":[]},"source":"A","target":"B"}),con)
        assert err.value.status_code==422
        assert ScenarioIn.model_validate({"name":"Flood 1","scenario_type":"Flood"}).status=="Planning"
        with pytest.raises(Exception): ScenarioIn.model_validate({"name":"x","scenario_type":"Flood"})
    finally: con.close()


def test_inventory_network_route_and_benchmark(tmp_path,monkeypatch):
    con=setup_db(tmp_path,monkeypatch)
    try:
        scenario=routes.create_scenario(ScenarioIn(name="Route case",scenario_type="Cyclone"),con)
        sid=scenario["id"]
        a=routes.create_road_node(RoadNodeIn(scenario_id=sid,name="Depot",x=20,y=30),con)
        b=routes.create_road_node(RoadNodeIn(scenario_id=sid,name="Ward A",x=200,y=140),con)
        routes.create_road_edge(RoadEdgeIn(scenario_id=sid,source_id=a["id"],target_id=b["id"],distance=7.5),con)
        graph=routes.network(sid,con)
        assert len(graph["edges"])==1
        out=routes.dijkstra_run(AlgorithmInput(scenario_id=sid,input={"graph_id":sid,"source":"Depot","target":"Ward A"}),con)
        assert out["output"]["path"]==["Depot","Ward A"] and out["output"]["cost"]==7.5
        resource=routes.create_resource(ResourceIn(scenario_id=sid,name="Water",category="Relief",unit="litres",unit_weight=1,available=30,divisible=True,value_score=5),con)
        assert resource["available"]==30 and routes.inventory(sid,con)[0]["name"]=="Water"
        bench=routes.benchmark(BenchmarkInput(algorithm="merge_sort",input_size=12,repeats=2,seed=6),con)
        assert len(bench["measurements_seconds"])==2 and routes.list_benchmarks(con)[0]["seed"]==6
        assert routes.list_benchmarks(con)[0]["python_version"]
    finally: con.close()


def test_bidirectional_roads_are_saved_together_and_routes_work_both_ways(tmp_path,monkeypatch):
    con=setup_db(tmp_path,monkeypatch)
    try:
        sid=routes.create_scenario(ScenarioIn(name="Two-way road case",scenario_type="Flood"),con)["id"]
        a=routes.create_road_node(RoadNodeIn(scenario_id=sid,name="Depot"),con)
        b=routes.create_road_node(RoadNodeIn(scenario_id=sid,name="Clinic"),con)
        roads=routes.create_bidirectional_road(RoadEdgeIn(scenario_id=sid,source_id=a["id"],target_id=b["id"],distance=12),con)
        assert len(roads)==2
        roads=routes.create_bidirectional_road(RoadEdgeIn(scenario_id=sid,source_id=a["id"],target_id=b["id"],distance=7),con)
        assert {road["distance"] for road in roads}=={7}
        assert len(routes.network(sid,con)["edges"])==2
        for source,target in (("Depot","Clinic"),("Clinic","Depot")):
            result=routes.dijkstra_run(AlgorithmInput(scenario_id=sid,input={"graph_id":sid,"source":source,"target":target}),con)
            assert result["output"]["cost"]==7
        with pytest.raises(HTTPException) as err:
            routes.create_bidirectional_road(RoadEdgeIn(scenario_id=sid,source_id=a["id"],target_id=a["id"],distance=1),con)
        assert err.value.status_code==422
    finally: con.close()


def test_openapi_lists_required_routes():
    paths=app.openapi()["paths"]
    for path in ("/api/health","/api/scenarios","/api/inventory","/api/road-edges",
                 "/api/algorithms/dijkstra","/api/algorithms/tsp","/api/algorithms/tsp/network","/api/benchmarks","/api/runs"):
        assert path in paths


def test_tour_from_saved_network_matches_exhaustive(tmp_path,monkeypatch):
    con=setup_db(tmp_path,monkeypatch)
    try:
        sid=routes.create_scenario(ScenarioIn(name="Tour case",scenario_type="Flood"),con)["id"]
        names=["Depot","Ward A","Ward B"]
        nodes=[routes.create_road_node(RoadNodeIn(scenario_id=sid,name=n),con) for n in names]
        weights=[[0,3,8],[3,0,4],[8,4,0]]
        for i in range(3):
            for j in range(3):
                if i!=j: routes.create_road_edge(RoadEdgeIn(scenario_id=sid,source_id=nodes[i]["id"],target_id=nodes[j]["id"],distance=weights[i][j]),con)
        body=AlgorithmInput(scenario_id=sid,input={"vertices":names,"start":"Depot"})
        result=routes.network_tsp_run(body,con)
        comparison=routes.network_tsp_compare(body,con)
        assert result["output"]["tour_names"][0]=="Depot"
        assert comparison["same_optimum"]
    finally: con.close()

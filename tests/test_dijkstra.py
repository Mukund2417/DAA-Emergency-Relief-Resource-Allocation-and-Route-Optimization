import math
import pytest
from app.algorithms.dijkstra import solve

def test_shortest_route_and_events():
    graph={"s":[("a",4),("b",1)],"a":[("s",4),("b",2),("t",1)],"b":[("s",1),("a",2),("t",5)],"t":[("a",1),("b",5)]}
    out=solve(graph,"s","t")
    assert out["path"] == ["s","b","a","t"]
    assert out["cost"] == 4
    assert out["events"]

def test_unreachable_and_source_destination():
    graph={"s":[("x",0)],"x":[("s",0)],"z":[]}
    assert math.isinf(solve(graph,"s","z")["cost"])
    assert solve(graph,"s","s")["path"] == ["s"]

def test_negative_and_unknown_vertices_rejected():
    with pytest.raises(ValueError): solve({"a":[("b",-1)],"b":[]},"a")
    with pytest.raises(ValueError): solve({"a":[]},"b")

def test_tied_routes_return_valid_minimum():
    g={"s":[("a",1),("b",1)],"a":[("s",1),("t",1)],"b":[("s",1),("t",1)],"t":[("a",1),("b",1)]}
    assert solve(g,"s","t")["cost"] == 2

import math
import pytest
from app.algorithms.bellman_ford import solve

def test_negative_edge_without_cycle():
    out=solve(["s","a","b"],[("s","a",4),("s","b",5),("a","b",-2)],"s")
    assert out["distances"]["b"] == 2

def test_disconnected_vertex():
    assert math.isinf(solve(["s","x"],[],"s")["distances"]["x"])

def test_negative_cycle_detected():
    with pytest.raises(ValueError): solve(["a","b"],[("a","b",-2),("b","a",1)],"a")

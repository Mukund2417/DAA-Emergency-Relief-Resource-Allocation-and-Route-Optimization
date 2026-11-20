import math
import pytest
from app.algorithms.tsp_branch_bound import solve
from app.algorithms.brute_force import tsp

def test_small_complete_graph_matches_exhaustive():
    matrix=[[None,10,15,20],[10,None,35,25],[15,35,None,30],[20,25,30,None]]
    out=solve(matrix,0); baseline=tsp(matrix,0)
    assert out["cost"] == baseline["cost"] == 80
    assert out["tour"][0] == out["tour"][-1] == 0

def test_different_start_and_single_node():
    matrix=[[None,2,9],[2,None,3],[9,3,None]]
    assert solve(matrix,1)["cost"] == 14
    assert solve([[0]])["tour"] == [0,0]

def test_no_tour_and_bad_matrix():
    out=solve([[None,1,None],[1,None,None],[None,None,None]])
    assert not out["tour"] and math.isinf(out["cost"])

def test_asymmetric_matrix_matches_exhaustive():
    matrix=[[None,3,9,8],[5,None,2,7],[6,4,None,3],[2,6,5,None]]
    out=solve(matrix,0); baseline=tsp(matrix,0)
    assert out["cost"]==baseline["cost"]
    assert out["tour"]==baseline["tour"] or out["cost"]==baseline["cost"]

def test_bad_matrix_and_negative_cost():
    with pytest.raises(ValueError): solve([[None,1],[2]])
    with pytest.raises(ValueError): solve([[None,-1],[-1,None]])

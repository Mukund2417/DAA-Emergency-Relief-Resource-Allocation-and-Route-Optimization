import pytest
from app.algorithms.zero_one_knapsack import solve, brute_force

def test_standard_and_brute_force_agree():
    items=[("a",10,60),("b",20,100),("c",30,120)]
    dp=solve(items,50); bf=brute_force(items,50)
    assert dp["value"] == bf["value"] == 220
    assert dp["weight"] <= 50

def test_zero_capacity_and_empty():
    assert solve([("x",1,9)],0)["value"] == 0
    assert solve([],10)["value"] == 0

def test_heavier_than_capacity_and_duplicate_weights():
    out=solve([("heavy",6,99),("a",3,5),("b",3,6)],3)
    assert out["value"] == 6

def test_many_small_cases_match_brute_force():
    for items in [[],[("a",2,3)],[("a",2,3),("b",3,4)],[("a",1,1),("b",1,1),("c",2,5)]]:
        for cap in range(5): assert solve(items,cap)["value"] == brute_force(items,cap)["value"]

def test_invalid_inputs():
    with pytest.raises(ValueError): solve([("x",0,1)],3)
    with pytest.raises(ValueError): solve([], -1)

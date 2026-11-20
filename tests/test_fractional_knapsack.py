import pytest
from app.algorithms.fractional_knapsack import Item, solve

def test_fractional_known_case():
    result = solve([Item("a",10,60),Item("b",20,100),Item("c",30,120)],50)
    assert result["value"] == pytest.approx(240)
    assert result["weight"] == pytest.approx(50)
    assert result["items"][-1]["fraction"] == pytest.approx(2/3)

@pytest.mark.parametrize("items,capacity", [([],5),([Item("a",2,4)],0)])
def test_fractional_empty_or_zero(items,capacity):
    assert solve(items,capacity)["value"] == 0

def test_fractional_capacity_exceeds_total():
    assert solve([Item("a",2,4)],9)["weight"] == pytest.approx(2)

def test_equal_ratio_is_stable():
    out=solve([Item("first",2,4),Item("second",1,2)],2)
    assert out["items"][0]["name"] == "first"

@pytest.mark.parametrize("weight",[0,-1,float("inf")])
def test_invalid_weight(weight):
    with pytest.raises(ValueError): solve([Item("bad",weight,1)],1)

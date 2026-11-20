import pytest
from app.algorithms.merge_sort import sort

@pytest.mark.parametrize("values",[[],[1],[1,2,3],[3,2,1],[2,1,2,-3,0]])
def test_sort_cases(values):
    assert sort(values)["sorted"] == sorted(values)

def test_stability_and_events():
    values=[("a",2),("b",1),("c",2)]
    result=sort(values,key=lambda x:x[1])
    assert result["sorted"] == [("b",1),("a",2),("c",2)]
    assert result["events"]

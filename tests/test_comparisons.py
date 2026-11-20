from app.services.comparison_service import compare

def test_equivalent_comparisons():
    knapsack={"capacity":50,"items":[["Water",10,60],["Food",20,100],["Kit",30,120]]}
    graph={"graph":{"Depot":[["North",4],["South",2]],"North":[["Depot",4],["South",1],["Clinic",5]],"South":[["Depot",2],["North",1],["Clinic",8]],"Clinic":[["North",5],["South",8]]},"source":"Depot","target":"Clinic"}
    matrix={"matrix":[[None,10,15,20],[10,None,35,25],[15,35,None,30],[20,25,30,None]],"start":0}
    values={"values":[12,4,19,3,8,8,-2]}
    assert compare("0/1 Knapsack",knapsack)["same_optimum"]
    assert compare("Shortest paths",graph)["same_optimum"]
    assert compare("TSP",matrix)["same_optimum"]
    assert compare("Sorting",values)["same_optimum"]

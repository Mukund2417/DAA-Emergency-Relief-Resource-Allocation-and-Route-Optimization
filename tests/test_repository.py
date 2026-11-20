from app.database import repository

def test_scenario_storage_uses_database(tmp_path):
    db=tmp_path / "test.db"
    sid=repository.create_scenario("Flood 01","Flood",path=db)
    repository.add_location(sid,"Ward A",4,path=db)
    row=repository.list_scenarios(path=db)[0]
    assert row["name"] == "Flood 01" and row["location_count"] == 1
    assert repository.dashboard_counts(path=db)["locations"] == 1
    repository.add_benchmark("Merge Sort",3,"sample",2,0.001,5,path=db)
    assert repository.recent_benchmarks(path=db)[0]["algorithm"] == "Merge Sort"

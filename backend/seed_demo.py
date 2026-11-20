"""Seed two clearly illustrative scenarios for a classroom presentation.

Run from the project root with: python -m backend.seed_demo
This is idempotent and does not remove or overwrite unrelated user data.
"""
from backend.app.models.database import connect, initialize
from backend.app.services.algorithm_service import execute, measured, save_run
from backend.app.services.benchmark_service import run_benchmark


def scenario(con, name, kind, description, status):
    row = con.execute("SELECT id FROM disaster_scenarios WHERE name=?", (name,)).fetchone()
    if row:
        sid = row["id"]
        con.execute("UPDATE disaster_scenarios SET scenario_type=?,description=?,status=? WHERE id=?",
                    (kind, description, status, sid))
    else:
        sid = con.execute("INSERT INTO disaster_scenarios(name,scenario_type,description,status) VALUES(?,?,?,?)",
                          (name, kind, description, status)).lastrowid
    return sid


def resource(con, scenario_id, name, category, unit, unit_weight, available, divisible, value_score):
    con.execute("INSERT INTO resource_types(name,category,unit,unit_weight,divisible,value_score) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET category=excluded.category,unit=excluded.unit,unit_weight=excluded.unit_weight,"
                "divisible=excluded.divisible,value_score=excluded.value_score",
                (name, category, unit, unit_weight, int(divisible), value_score))
    rid = con.execute("SELECT id FROM resource_types WHERE name=?", (name,)).fetchone()[0]
    con.execute("INSERT INTO resource_inventory(scenario_id,resource_type_id,available) VALUES(?,?,?) "
                "ON CONFLICT(scenario_id,resource_type_id) DO UPDATE SET available=excluded.available",
                (scenario_id, rid, available))
    return rid


def location(con, scenario_id, identifier, name, priority, latitude, longitude, x, y):
    con.execute("INSERT INTO affected_locations(scenario_id,identifier,name,priority,latitude,longitude,x,y) VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(scenario_id,name) DO UPDATE SET identifier=excluded.identifier,priority=excluded.priority,"
                "latitude=excluded.latitude,longitude=excluded.longitude,x=excluded.x,y=excluded.y",
                (scenario_id, identifier, name, priority, latitude, longitude, x, y))
    return con.execute("SELECT id FROM affected_locations WHERE scenario_id=? AND name=?", (scenario_id, name)).fetchone()[0]


def road_node(con, scenario_id, name, location_id, x, y):
    con.execute("INSERT INTO road_nodes(scenario_id,location_id,name,x,y) VALUES(?,?,?,?,?) "
                "ON CONFLICT(scenario_id,name) DO UPDATE SET location_id=excluded.location_id,x=excluded.x,y=excluded.y",
                (scenario_id, location_id, name, x, y))
    return con.execute("SELECT id FROM road_nodes WHERE scenario_id=? AND name=?", (scenario_id, name)).fetchone()[0]


def build_scenario(con, *, name, kind, description, status, locs, inventory, links):
    sid = scenario(con, name, kind, description, status)
    resource_ids = {entry[0]: resource(con, sid, *entry) for entry in inventory}
    node_ids = {}
    for entry in locs:
        loc_id = location(con, sid, *entry)
        node_ids[entry[1]] = road_node(con, sid, entry[1], loc_id, entry[5], entry[6])
    for location_name, demands in links:
        loc_id = con.execute("SELECT id FROM affected_locations WHERE scenario_id=? AND name=?", (sid, location_name)).fetchone()[0]
        for resource_name, quantity in demands.items():
            con.execute("INSERT INTO location_demands(location_id,resource_type_id,quantity) VALUES(?,?,?) "
                        "ON CONFLICT(location_id,resource_type_id) DO UPDATE SET quantity=excluded.quantity",
                        (loc_id, resource_ids[resource_name], quantity))
    return sid, node_ids


def add_roads(con, scenario_id, node_ids, edges):
    for source, target, km in edges:
        con.execute("INSERT INTO road_edges(scenario_id,source_id,target_id,distance,blocked) VALUES(?,?,?,?,0) "
                    "ON CONFLICT(scenario_id,source_id,target_id) DO UPDATE SET distance=excluded.distance,blocked=0",
                    (scenario_id, node_ids[source], node_ids[target], km))


def save_demo_run(con, sid, algorithm, data):
    if con.execute("SELECT 1 FROM algorithm_runs WHERE scenario_id=? AND algorithm=? LIMIT 1", (sid, algorithm)).fetchone():
        return
    output, elapsed = measured(algorithm, data)
    save_run(con, algorithm, data, output, elapsed, sid)


def main():
    initialize()
    con = connect()
    try:
        with con:
            # Recover these two seed names if this script was run in a shell whose
            # legacy code page replaced the middle-dot character.
            con.execute("UPDATE disaster_scenarios SET name='Odisha Cyclone Relief - Illustrative' WHERE name LIKE 'Odisha Cyclone Relief%'")
            con.execute("UPDATE disaster_scenarios SET name='Assam Flood Response - Illustrative' WHERE name LIKE 'Assam Flood Response%'")
            # These teaching values and road costs are illustrative. They are not an official
            # incident record, live needs assessment, or navigation recommendation.
            odisha, odisha_nodes = build_scenario(
                con, name="Odisha Cyclone Relief - Illustrative", kind="Cyclone",
                description="Classroom case: organize supplies and a small delivery graph for coastal Odisha. All quantities, priorities and edge costs are illustrative, not official incident data.",
                status="Planning",
                locs=[
                    ("OD-DEPOT", "Bhubaneswar Supply Depot", 3, 20.2961, 85.8245, 100, 90),
                    ("OD-PURI", "Puri Relief Hub", 5, 19.8135, 85.8312, 420, 180),
                    ("OD-BLS", "Balasore Relief Hub", 4, 21.4942, 86.9336, 300, 330),
                    ("OD-KND", "Kendrapara Relief Hub", 4, 20.5017, 86.4223, 560, 140),
                ],
                inventory=[
                    ("Water cans", "Relief", "cans", 10.0, 120, False, 8.0),
                    ("Food packs", "Relief", "packs", 1.0, 260, True, 9.0),
                    ("First-aid kits", "Medical", "kits", 3.0, 48, False, 10.0),
                ],
                links=[("Bhubaneswar Supply Depot", {}), ("Puri Relief Hub", {"Water cans": 65, "Food packs": 140, "First-aid kits": 18}),
                       ("Balasore Relief Hub", {"Water cans": 45, "Food packs": 90, "First-aid kits": 22}),
                       ("Kendrapara Relief Hub", {"Water cans": 55, "Food packs": 110, "First-aid kits": 20})])
            add_roads(con, odisha, odisha_nodes, [
                ("Bhubaneswar Supply Depot", "Puri Relief Hub", 60), ("Puri Relief Hub", "Bhubaneswar Supply Depot", 60),
                ("Bhubaneswar Supply Depot", "Kendrapara Relief Hub", 90), ("Kendrapara Relief Hub", "Bhubaneswar Supply Depot", 90),
                ("Bhubaneswar Supply Depot", "Balasore Relief Hub", 205), ("Balasore Relief Hub", "Bhubaneswar Supply Depot", 205),
                ("Puri Relief Hub", "Kendrapara Relief Hub", 115), ("Kendrapara Relief Hub", "Puri Relief Hub", 115),
                ("Kendrapara Relief Hub", "Balasore Relief Hub", 145), ("Balasore Relief Hub", "Kendrapara Relief Hub", 145)])

            assam, assam_nodes = build_scenario(
                con, name="Assam Flood Response - Illustrative", kind="Flood",
                description="Classroom case: prioritize relief supplies and compare routes among Assam planning locations. All quantities, priorities and edge costs are illustrative, not official incident data.",
                status="Active",
                locs=[
                    ("AS-DEPOT", "Guwahati Supply Depot", 3, 26.1445, 91.7362, 110, 100),
                    ("AS-BRP", "Barpeta Relief Hub", 5, 26.3220, 91.0063, 360, 200),
                    ("AS-MRG", "Morigaon Relief Hub", 4, 26.2520, 92.3420, 310, 350),
                    ("AS-NGN", "Nagaon Relief Hub", 4, 26.3480, 92.6840, 280, 500),
                ],
                inventory=[
                    ("Water cans", "Relief", "cans", 10.0, 150, False, 8.0),
                    ("Food packs", "Relief", "packs", 1.0, 320, True, 9.0),
                    ("First-aid kits", "Medical", "kits", 3.0, 60, False, 10.0),
                ],
                links=[("Guwahati Supply Depot", {}), ("Barpeta Relief Hub", {"Water cans": 75, "Food packs": 170, "First-aid kits": 24}),
                       ("Morigaon Relief Hub", {"Water cans": 65, "Food packs": 135, "First-aid kits": 20}),
                       ("Nagaon Relief Hub", {"Water cans": 55, "Food packs": 120, "First-aid kits": 18})])
            add_roads(con, assam, assam_nodes, [
                ("Guwahati Supply Depot", "Barpeta Relief Hub", 95), ("Barpeta Relief Hub", "Guwahati Supply Depot", 95),
                ("Guwahati Supply Depot", "Morigaon Relief Hub", 78), ("Morigaon Relief Hub", "Guwahati Supply Depot", 78),
                ("Guwahati Supply Depot", "Nagaon Relief Hub", 120), ("Nagaon Relief Hub", "Guwahati Supply Depot", 120),
                ("Barpeta Relief Hub", "Morigaon Relief Hub", 145), ("Morigaon Relief Hub", "Barpeta Relief Hub", 145),
                ("Morigaon Relief Hub", "Nagaon Relief Hub", 63), ("Nagaon Relief Hub", "Morigaon Relief Hub", 63)])

            save_demo_run(con, assam, "dijkstra", {"graph": {
                "Guwahati Supply Depot": [("Barpeta Relief Hub", 95), ("Morigaon Relief Hub", 78), ("Nagaon Relief Hub", 120)],
                "Barpeta Relief Hub": [("Guwahati Supply Depot", 95), ("Morigaon Relief Hub", 145)],
                "Morigaon Relief Hub": [("Guwahati Supply Depot", 78), ("Barpeta Relief Hub", 145), ("Nagaon Relief Hub", 63)],
                "Nagaon Relief Hub": [("Guwahati Supply Depot", 120), ("Morigaon Relief Hub", 63)]},
                "source": "Guwahati Supply Depot", "target": "Nagaon Relief Hub"})
            save_demo_run(con, assam, "fractional_knapsack", {"capacity": 100, "items": [
                {"name": "Water cans", "weight": 10, "value": 8},
                {"name": "Food packs", "weight": 1, "value": 9},
                {"name": "First-aid kits", "weight": 3, "value": 10}]})
            save_demo_run(con, assam, "knapsack_01", {"capacity": 24, "items": [
                ["Water cans", 10, 8], ["Food pack carton", 8, 35], ["First-aid case", 9, 42], ["Shelter kit", 12, 50]]})
            save_demo_run(con, assam, "tsp_branch_bound", {"matrix": [
                [None, 95, 78, 120], [95, None, 145, 180], [78, 145, None, 63], [120, 180, 63, None]], "start": 0})

            if not con.execute("SELECT 1 FROM benchmark_runs LIMIT 1").fetchone():
                result = run_benchmark("merge_sort", 80, 42, 5)
                cur = con.execute("INSERT INTO benchmark_runs(algorithm,input_size,seed,repeat_count,median_seconds,python_version,platform) VALUES(?,?,?,?,?,?,?)",
                                  (result["algorithm"], result["input_size"], result["seed"], result["repeat_count"], result["median_seconds"], result["python_version"], result["platform"]))
                for i, seconds in enumerate(result["measurements_seconds"], 1):
                    con.execute("INSERT INTO benchmark_measurements(benchmark_id,repetition,elapsed_seconds) VALUES(?,?,?)", (cur.lastrowid, i, seconds))

        print("Demo scenarios ready: 2 scenarios, 8 locations, 6 saved stock rows, directed road networks, algorithm examples, and one measured benchmark.")
        print("All scenario figures and road costs are illustrative; verify or replace them before treating them as real planning data.")
    finally:
        con.close()


if __name__ == "__main__":
    main()

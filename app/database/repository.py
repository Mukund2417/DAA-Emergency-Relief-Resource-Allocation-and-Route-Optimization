"""Small parameterized repository methods used by the application."""
import json
from .connection import transaction, DB_PATH


def create_scenario(name: str, disaster_type: str, notes: str = "", path=DB_PATH) -> int:
    if not name.strip(): raise ValueError("Scenario name is required")
    with transaction(path) as con:
        cur = con.execute("INSERT INTO disaster_scenarios(name, disaster_type, notes) VALUES(?,?,?)",
                          (name.strip(), disaster_type, notes.strip()))
        return int(cur.lastrowid)


def list_scenarios(path=DB_PATH) -> list[dict]:
    with transaction(path) as con:
        return [dict(row) for row in con.execute(
            "SELECT s.*, COUNT(l.id) AS location_count FROM disaster_scenarios s "
            "LEFT JOIN locations l ON l.scenario_id=s.id GROUP BY s.id ORDER BY s.created_at DESC, s.id DESC")]


def add_location(scenario_id: int, name: str, priority: int = 3, path=DB_PATH) -> int:
    with transaction(path) as con:
        cur = con.execute("INSERT INTO locations(scenario_id,name,priority) VALUES(?,?,?)",
                          (scenario_id, name.strip(), priority))
        return int(cur.lastrowid)


def add_inventory_item(name: str, category: str, weight: float, quantity: float,
                       value: float, path=DB_PATH) -> int:
    with transaction(path) as con:
        cur = con.execute("INSERT INTO inventory_items(name,category,weight,quantity,value) VALUES(?,?,?,?,?)",
                          (name.strip(), category.strip(), weight, quantity, value))
        return int(cur.lastrowid)


def list_inventory(path=DB_PATH) -> list[dict]:
    with transaction(path) as con:
        return [dict(row) for row in con.execute("SELECT * FROM inventory_items ORDER BY category,name")]


def save_experiment(name: str, algorithm: str, inputs: dict, output: dict,
                    elapsed: float, operations: int, scenario_id=None, path=DB_PATH) -> int:
    with transaction(path) as con:
        cur = con.execute("INSERT INTO experiments(scenario_id,name,input_json) VALUES(?,?,?)",
                          (scenario_id, name, json.dumps(inputs)))
        experiment_id = int(cur.lastrowid)
        con.execute("INSERT INTO algorithm_results(experiment_id,algorithm,output_json,elapsed_seconds,operation_count) VALUES(?,?,?,?,?)",
                    (experiment_id, algorithm, json.dumps(output, default=str), elapsed, operations))
        return experiment_id


def dashboard_counts(path=DB_PATH) -> dict[str, int]:
    with transaction(path) as con:
        return {"scenarios": con.execute("SELECT COUNT(*) FROM disaster_scenarios").fetchone()[0],
                "locations": con.execute("SELECT COUNT(*) FROM locations").fetchone()[0],
                "inventory": con.execute("SELECT COUNT(*) FROM inventory_items").fetchone()[0],
                "experiments": con.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]}


def recent_experiments(limit: int = 20, path=DB_PATH) -> list[dict]:
    with transaction(path) as con:
        return [dict(row) for row in con.execute(
            "SELECT e.id, e.name, e.created_at, r.algorithm, r.elapsed_seconds, r.operation_count "
            "FROM experiments e JOIN algorithm_results r ON r.experiment_id=e.id "
            "ORDER BY e.id DESC LIMIT ?", (limit,))]


def add_benchmark(algorithm: str, input_size: int, category: str, repeats: int,
                  elapsed: float, operations: int, path=DB_PATH) -> int:
    with transaction(path) as con:
        cur = con.execute("INSERT INTO benchmark_results(algorithm,input_size,category,repeat_count,elapsed_seconds,operation_count) VALUES(?,?,?,?,?,?)",
                          (algorithm,input_size,category,repeats,elapsed,operations))
        return int(cur.lastrowid)


def recent_benchmarks(limit: int = 20, path=DB_PATH) -> list[dict]:
    with transaction(path) as con:
        return [dict(row) for row in con.execute(
            "SELECT * FROM benchmark_results ORDER BY id DESC LIMIT ?", (limit,))]

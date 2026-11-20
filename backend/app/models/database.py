"""Normalized SQLite schema and connection helpers for the web application."""
import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(os.getenv("DAA_WEB_DB", Path(__file__).resolve().parents[2] / "data" / "webapp.db"))

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS disaster_scenarios (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, scenario_type TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Planning'
 CHECK(status IN ('Planning','Active','Closed')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS affected_locations (
 id INTEGER PRIMARY KEY, scenario_id INTEGER NOT NULL REFERENCES disaster_scenarios(id) ON DELETE CASCADE,
 identifier TEXT, name TEXT NOT NULL, priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
 latitude REAL, longitude REAL, x REAL NOT NULL DEFAULT 100, y REAL NOT NULL DEFAULT 100,
 UNIQUE(scenario_id,name)
);
CREATE TABLE IF NOT EXISTS resource_types (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL,
 unit TEXT NOT NULL, unit_weight REAL NOT NULL DEFAULT 1 CHECK(unit_weight > 0), divisible INTEGER NOT NULL CHECK(divisible IN (0,1)),
 value_score REAL NOT NULL CHECK(value_score >= 0)
);
CREATE TABLE IF NOT EXISTS resource_inventory (
 id INTEGER PRIMARY KEY, scenario_id INTEGER REFERENCES disaster_scenarios(id) ON DELETE CASCADE,
 resource_type_id INTEGER NOT NULL REFERENCES resource_types(id), available REAL NOT NULL CHECK(available >= 0),
 UNIQUE(scenario_id,resource_type_id)
);
CREATE TABLE IF NOT EXISTS location_demands (
 id INTEGER PRIMARY KEY, location_id INTEGER NOT NULL REFERENCES affected_locations(id) ON DELETE CASCADE,
 resource_type_id INTEGER NOT NULL REFERENCES resource_types(id), quantity REAL NOT NULL CHECK(quantity >= 0),
 UNIQUE(location_id,resource_type_id)
);
CREATE TABLE IF NOT EXISTS road_nodes (
 id INTEGER PRIMARY KEY, scenario_id INTEGER NOT NULL REFERENCES disaster_scenarios(id) ON DELETE CASCADE,
 location_id INTEGER REFERENCES affected_locations(id) ON DELETE SET NULL,
 name TEXT NOT NULL, x REAL NOT NULL DEFAULT 100, y REAL NOT NULL DEFAULT 100,
 UNIQUE(scenario_id,name)
);
CREATE TABLE IF NOT EXISTS road_edges (
 id INTEGER PRIMARY KEY, scenario_id INTEGER NOT NULL REFERENCES disaster_scenarios(id) ON DELETE CASCADE,
 source_id INTEGER NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
 target_id INTEGER NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
 distance REAL NOT NULL CHECK(distance >= 0), blocked INTEGER NOT NULL DEFAULT 0 CHECK(blocked IN (0,1)),
 CHECK(source_id <> target_id), UNIQUE(scenario_id,source_id,target_id)
);
CREATE TABLE IF NOT EXISTS algorithm_runs (
 id INTEGER PRIMARY KEY, scenario_id INTEGER REFERENCES disaster_scenarios(id) ON DELETE SET NULL,
 algorithm TEXT NOT NULL, input_json TEXT NOT NULL, output_json TEXT NOT NULL,
 elapsed_seconds REAL NOT NULL CHECK(elapsed_seconds >= 0), operations INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS allocation_results (
 run_id INTEGER PRIMARY KEY REFERENCES algorithm_runs(id) ON DELETE CASCADE,
 result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS route_results (
 run_id INTEGER PRIMARY KEY REFERENCES algorithm_runs(id) ON DELETE CASCADE,
 result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS benchmark_runs (
 id INTEGER PRIMARY KEY, algorithm TEXT NOT NULL, input_size INTEGER NOT NULL,
 seed INTEGER NOT NULL, repeat_count INTEGER NOT NULL, median_seconds REAL NOT NULL,
    python_version TEXT NOT NULL DEFAULT '', platform TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS benchmark_measurements (
 id INTEGER PRIMARY KEY, benchmark_id INTEGER NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
 repetition INTEGER NOT NULL, elapsed_seconds REAL NOT NULL CHECK(elapsed_seconds >= 0)
);
"""


def connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def initialize() -> None:
    with connect() as con:
        con.executescript(SCHEMA)
        columns={row[1] for row in con.execute("PRAGMA table_info(resource_types)")}
        if "unit_weight" not in columns:
            con.execute("ALTER TABLE resource_types ADD COLUMN unit_weight REAL NOT NULL DEFAULT 1 CHECK(unit_weight > 0)")
        benchmark_columns={row[1] for row in con.execute("PRAGMA table_info(benchmark_runs)")}
        if "python_version" not in benchmark_columns: con.execute("ALTER TABLE benchmark_runs ADD COLUMN python_version TEXT NOT NULL DEFAULT ''")
        if "platform" not in benchmark_columns: con.execute("ALTER TABLE benchmark_runs ADD COLUMN platform TEXT NOT NULL DEFAULT ''")

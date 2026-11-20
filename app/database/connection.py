"""SQLite initialization with foreign keys and transaction-safe connections."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "application.db"


def connect(path: str | Path = DB_PATH) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


@contextmanager
def transaction(path: str | Path = DB_PATH):
    con = connect(path)
    try:
        with con:
            yield con
    finally:
        con.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS disaster_scenarios (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, disaster_type TEXT NOT NULL,
 notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS locations (
 id INTEGER PRIMARY KEY, scenario_id INTEGER NOT NULL REFERENCES disaster_scenarios(id) ON DELETE CASCADE,
 name TEXT NOT NULL, priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
 latitude REAL, longitude REAL, UNIQUE(scenario_id, name)
);
CREATE TABLE IF NOT EXISTS road_edges (
 id INTEGER PRIMARY KEY, scenario_id INTEGER NOT NULL REFERENCES disaster_scenarios(id) ON DELETE CASCADE,
 from_location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
 to_location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
 distance REAL NOT NULL CHECK(distance >= 0), available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0,1)),
 CHECK(from_location_id <> to_location_id), UNIQUE(scenario_id, from_location_id, to_location_id)
);
CREATE TABLE IF NOT EXISTS inventory_items (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL,
 weight REAL NOT NULL CHECK(weight > 0), quantity REAL NOT NULL CHECK(quantity >= 0),
 value REAL NOT NULL CHECK(value >= 0)
);
CREATE TABLE IF NOT EXISTS supply_requirements (
 id INTEGER PRIMARY KEY, location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
 item_name TEXT NOT NULL, quantity REAL NOT NULL CHECK(quantity >= 0), priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5)
);
CREATE TABLE IF NOT EXISTS vehicles (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, capacity REAL NOT NULL CHECK(capacity >= 0)
);
CREATE TABLE IF NOT EXISTS experiments (
 id INTEGER PRIMARY KEY, scenario_id INTEGER REFERENCES disaster_scenarios(id) ON DELETE SET NULL,
 name TEXT NOT NULL, input_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS algorithm_results (
 id INTEGER PRIMARY KEY, experiment_id INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
 algorithm TEXT NOT NULL, output_json TEXT NOT NULL, elapsed_seconds REAL NOT NULL CHECK(elapsed_seconds >= 0),
 operation_count INTEGER NOT NULL DEFAULT 0 CHECK(operation_count >= 0)
);
CREATE TABLE IF NOT EXISTS benchmark_results (
 id INTEGER PRIMARY KEY, algorithm TEXT NOT NULL, input_size INTEGER NOT NULL,
 category TEXT NOT NULL, repeat_count INTEGER NOT NULL CHECK(repeat_count > 0),
 elapsed_seconds REAL NOT NULL CHECK(elapsed_seconds >= 0), operation_count INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

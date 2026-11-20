# Web Application Architecture

The website is a React 18 + TypeScript + Vite client. A single dashboard shell owns responsive navigation and route rendering. Feature pages call a centralized `services/api.ts` client. Backend responses are authoritative; the browser does not calculate paths or fabricate dashboard totals.

FastAPI exposes `/api` endpoints and OpenAPI docs at `/docs`. Pydantic validates request boundaries. Algorithm API adapters call the preserved independent modules in the root `app/algorithms/` package. Algorithm logic has no FastAPI dependency. The old PySide6 prototype remains in root `app/ui` and is a separate secondary application.

The browser uses Recharts for saved measured benchmark medians and React Flow for editing/displaying persisted road nodes and edges. Dijkstra and Bellman-Ford always execute in Python. Route output is saved by the backend; the network page highlights the latest saved Dijkstra path for the selected scenario.

## SQLite model

- `disaster_scenarios` owns affected locations, inventory, road nodes/edges and may link to algorithm runs.
- `affected_locations` belongs to one scenario and can reference named demands in `location_demands`.
- `resource_types` defines category, unit, unit weight, divisibility and objective score. `resource_inventory` stores quantity for a scenario (or shared stock when scenario is null).
- `road_nodes` belong to a scenario and optionally link to an affected location. `road_edges` connect two nodes, store non-negative directed distance and blocked status.
- `algorithm_runs` stores inputs, actual outputs, measured time and operation count. Allocation/route details are separated in `allocation_results` and `route_results`.
- `benchmark_runs` stores algorithm, input size, seed, repeats, median, Python version and platform. `benchmark_measurements` stores each sample.

Schema initialization uses `CREATE TABLE IF NOT EXISTS` and small additive column migrations. Foreign keys are enabled for each connection. No sample rows are inserted automatically.

## Assumptions and safety

Road edges are directed; add reverse edges for bidirectional roads. Blocked edges are excluded from Dijkstra/Bellman-Ford. Distance is a user-defined edge cost in a consistent unit, not live travel time. Fractional items are divisible; 0/1 packages are not. TSP accepts finite non-negative matrices, symmetric or asymmetric, and is limited to ten locations. The app is not a live dispatch system.

## Local development

Run FastAPI and Vite separately using the commands in the root README. Vite proxies `/api` to localhost:8000. FastAPI serves `frontend/dist` if a build exists.
# Live data

The optional India Live Data page uses the public Open-Meteo geocoding API to search Indian places and the Open-Meteo forecast API for current model-based weather at the selected coordinates. FastAPI proxies requests, limits lookup coordinates to India's approximate bounding rectangle, applies a ten-second upstream timeout, and returns source and retrieval timestamps. No API key or live data is written to the project's SQLite database. Weather is contextual information, not an official hazard alert.

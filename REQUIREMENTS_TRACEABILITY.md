# Requirements Traceability

Status: **Implemented** means source and API/algorithm-level behavior exists; it does not imply a browser-level build or visual check. **Verified** means executed by an appropriate automated check. **Pending** means blocked or requires student data.

| Requirement | Implementation | Status / evidence |
|---|---|---|
| Preserve prior DAA work and desktop prototype | Root `app/`, `main.py`, and tests retained | Verified: 38 total Python tests now pass |
| Website as primary app | `frontend/src/`, API at `backend/app/` | Production build passes; dashboard HTTP endpoint responds; browser visual walkthrough pending |
| Merge Sort, Fractional/0-1 Knapsack, Dijkstra, Bellman-Ford and TSP | Root algorithms with thin backend adapters | Verified through unit tests and synchronous route tests |
| TSP symmetric/asymmetric admissible bounds | `app/algorithms/tsp_branch_bound.py` | Verified against brute force on small symmetric/asymmetric cases |
| FastAPI health, CRUD, algorithm and comparison routes | `backend/app/api/routes.py` | Route functions and OpenAPI route listing verified; HTTP transport pending |
| SQLite scenarios, locations, inventory, demands and road graph | `backend/app/models/database.py` and routes | Verified persistence and network-route test cases |
| Fixed-seed benchmark and measured history | `backend/app/services/benchmark_service.py` | Verified measurements are persisted; frontend chart integration pending |
| Scenario-based network shortest route and tour | Route and network APIs + React Flow/Tour pages | Python route check verified; browser interactions pending |
| Recharts actual benchmark values | `frontend/src/pages/Performance.tsx` | Production build passes; chart consumes saved medians by algorithm and input size; browser render pending |
| India-specific live public API data | `backend/app/api/india.py`, `frontend/src/pages/IndiaLiveData.tsx` | Local HTTP search and current Guwahati weather lookup both returned live Open-Meteo data; browser presentation pending |
| CSV/PDF scenario result export | `/api/reports/{id}.csv|pdf` and Reports page | Route code tested; PDF header checked, not visually rendered |
| Twelve browser routes and responsive shell | `frontend/src/App.tsx`, pages/layouts/styles | `npm run build` passes; page-level chunks emitted; browser visual walkthrough pending |
| College A4 report | `reports/DAA_Minor_Project_Report.docx`, `.pdf` | Eight image headings used and all six rendered pages inspected; guideline PDF and student details pending |
| Demo and viva materials | `docs/DEMO_SCRIPT.md`, `VIVA_QUESTIONS_AND_ANSWERS.md` | Implemented; team contributions need student confirmation |
| Git branch/status audit | `PROJECT_AUDIT.md` | Verified: folder has no `.git`, branch or history |

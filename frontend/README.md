# React web client

Install dependencies using `npm install`, then run `npm run dev`. The app uses Vite on `http://127.0.0.1:5173` and proxies `/api` to the FastAPI server on port 8000. For release checks run `npm run build`.

The dashboard shell takes structural inspiration from Shadcn Dashboard; no dashboard application files were copied. Its MIT notice asks downstream projects to credit Shadcn Dashboard; the footer includes the requested link. Reusable local controls are kept in `src/components/ui.tsx`. Recharts uses saved benchmark results; React Flow displays saved road nodes and edges.
